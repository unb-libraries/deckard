# Source Content Considerations

## Poor Performing Content
Content sets should be curated if possible. Bulk crawling of unorganized content sets sets a ceiling on performance. Consider GIGO.

## Web Collectors

### Tables
Several approaches
table to CSV

"You simply pass csv-formatted text string preferably wrapped within a markdown codeblock syntax. In my experience both commercial and open-source models work quite well in the domain of NLP. If your tabular data is numerically heavy and results seem inconsistent try quantizing them into ordinal categories since after all this is a language model."


### Types of pages

Link-list style pages offer little to the LLM
https://lib.unb.ca/gddm/data/provinces-territories-municipalities

'Index' style pages that link to pages within the dataset

https://lib.unb.ca/node/172


'Hours' pages are best handled with pre-filtering in a multi-step
https://lib.unb.ca/node/1145


Input Forms
https://lib.unb.ca/node/1199


FAQ pages with no text
https://lib.unb.ca/node/1317


Video pages with little to no context or transcript
https://lib.unb.ca/node/1344
