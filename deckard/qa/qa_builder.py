import yaml

from logging import Logger
from pydantic import ValidationError

from deckard.core import load_class
from deckard.core.utils import gen_uuid
from deckard.qa.qa_validator import QAFile

class QABuilder:
    def __init__(
        self,
        config: dict,
        log: Logger
    ):
        self.log = log
        self.config = config
        self._init_qa_builder_components()
        self._load_questions_from_file()

    def build(self) -> None:
        if self.config['qa']['database'] and self.config['qa']['questions']:
            self.qa_database.flush_data()
            self.log.info("Building QA items")
            question_id = 0
            is_first_question = True
            for question in self.config['qa']['questions']:
                for query in question.queries:
                    self.log.info("Processing question: %s", query)
                    question_data = {}
                    question_data['id'] = gen_uuid()
                    question_data['question'] = query

                    for key, value in question.dict().items():
                        if key != 'queries':
                            question_data[key] = value

                    question_data['vector'] = self.qa_encoder.encode(query)
                    self.qa_database.add_qa_question(
                        question_data,
                        is_first_question
                    )
                    if is_first_question:
                        is_first_question = False
                    question_id += 1
        self.log.info("Processed %s questions.", question_id)
        self.log.info("QA Pipeline Processing Complete.")

    def _init_qa_builder_components(self) -> None:
        """Initializes the components for building the QA pipeline."""
        if self.config['qa']['database']:
            self.log.info("Using QA database %s", self.config['qa']['database']['name'])
            self.qa_database = load_class(
                self.config['qa']['database']['module_name'],
                self.config['qa']['database']['class_name'],
                [
                    self.config['qa']['database']['name'],
                    self.log,
                    True
                ]
            )

            self.qa_encoder = load_class(
                self.config['qa']['encoder']['module_name'],
                self.config['qa']['encoder']['class_name'],
                [
                    self.config['qa']['encoder']['model'],
                    self.log
                ]
            )

    def _load_questions_from_file(self) -> None:
        """Loads and validates questions from the external qa.yml file."""
        questions_file = self.config['qa'].get('questions_file', 'qa.yml')
        try:
            with open(questions_file, 'r') as file:
                questions_data = yaml.safe_load(file)
                # Validate using Pydantic
                validated_data = QAFile(**questions_data)
                self.config['qa']['questions'] = validated_data.questions
                self.log.info("Loaded and validated questions from %s", questions_file)
        except FileNotFoundError:
            self.log.error("Questions file %s not found.", questions_file)
            self.config['qa']['questions'] = []
        except yaml.YAMLError as e:
            self.log.error("Error parsing questions file %s: %s", questions_file, str(e))
            self.config['qa']['questions'] = []
        except ValidationError as e:
            self.log.error("Validation error in questions file %s: %s", questions_file, str(e))
            self.config['qa']['questions'] = []
