from flask import Response
from os import makedirs

from deckard.core import json_dumper, load_class
from deckard.core.time import cur_timestamp
from deckard.core.config import get_rag_pipeline, get_data_dir
from deckard.core.utils import gen_uuid

class ApiResponse:
    def __init__(self, *, query=None, pipeline=None, exclusive_mode=None, timings=None, logger=None):
        self.timings = timings
        self.logger = logger
        self.response = {
            'id': gen_uuid(),
            'query': query,
            'pipeline': pipeline,
            'exclusive_mode': exclusive_mode
        }

    @classmethod
    def new(cls, *, query=None, pipeline=None, exclusive_mode=None, timings=None, logger=None):
        return cls(query=query, pipeline=pipeline, exclusive_mode=exclusive_mode, timings=timings, logger=logger)

    def update(self, d):
        self.response.update(d)

    def handle_error(self):
        if 'error' in self.response:
            self.logger.error("Error in LLM query:")
            self.logger.error(self.response['error'])
            self.response['is_answer'] = False
            return Response(json_dumper(self.response, pretty=False), status=500, mimetype='application/json')
        return None

    def process_response(self):
        """Post-processes the response if needed (RAG pipeline, etc)."""
        if self.response.get('is_answer') and self.response.get('qa_answered') != True:
            config = get_rag_pipeline(self.response.get('pipeline'))['rag']
            response_processor = load_class(
                config['response_processor']['module_name'],
                config['response_processor']['class_name'],
                [self.response['response'], self.logger]
            )
            self.response['response'] = response_processor.get_processed_response()
        return self.response

    def render(self):
        error_response = self.handle_error()
        if error_response:
            return error_response

        self.process_response()
        self.response['timings'] = self.timings.get_timings() if self.timings else {}

        self.finalize()
        self.write_response_disk()
        return Response(json_dumper(self.response, pretty=False), status=200, mimetype='application/json')

    def finalize(self):
        self.response['timings'] = self.timings.get_timings() if self.timings else {}

    # @TODO - Hardcoded: Should be moved to config
    def write_response_disk(self) -> None:
        """Writes the response data to a file."""
        data_dir = get_data_dir()
        summary_response_dir = f"{data_dir}/deckard_responses"
        makedirs(summary_response_dir, exist_ok=True)
        final_filepath = f"{summary_response_dir}/response_{cur_timestamp()}.json"
        with open(final_filepath, 'w') as f:
            f.write(json_dumper(self.response, pretty=True))

    # Timing wrapper methods
    def start_timing(self, *args, **kwargs):
        return self.timings.start_timing(*args, **kwargs)

    def time_block(self, *args, **kwargs):
        return self.timings.time_block(*args, **kwargs)

    def compound_time_block(self, *args, **kwargs):
        return self.timings.compound_time_block(*args, **kwargs)

    def reset_timing(self, *args, **kwargs):
        return self.timings.reset_timing(*args, **kwargs)

    def finalize_timing(self, *args, **kwargs):
        return self.timings.finalize_timing(*args, **kwargs)
