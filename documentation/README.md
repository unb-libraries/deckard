# Documentation
WORK IN PROGRESS

## Topics
* [Technical Prerequisites, Guidance](./TECHNICAL_PREREQUISITE_GUIDANCE.md "Technical Prerequisites, Guidance")
* [Configuration Considerations](./CONFIGURATION_CONSIDERATIONS.md "Project Design Considerations")
* [Project Design Considerations](./PROJECT_DESIGN_CONSIDERATIONS.md "Project Design Considerations")

## Modules
Deckard's module architecture is based on a core concept of 'data units': representations of one or more ideas in textual form.

### Collectors
Collectors collect data units from source(s) and transform them into pure textual representations. Modules can be written to access data via the web, from a database, or another endpoint. Workflows can have multiple collectors.

### Chunkers
Chunkers divide single data units into 'chunks': elements created to:

* Segregate semantic concepts within the data unit for improved context.
* Reduce unit size to allow multiple pieces of data to be included in a context space of LLMs.

### Transformers
Transformers map chunks into vector representations.

### Database
Database modules provide API interfaces into vector database storage.

### Interfaces
Interfaces expose data to users.

### Processors
Processors provide pipelines that move data between one or many other module types.

