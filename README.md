# DTSCodingDB
A repo for the project combining achievement in AS91906 &amp; AS91902


--- 

## Planning
##### Evidence needed/planning notes:
* [ ] Iterative improvement proof \(git commit history can be part of this, but perhaps tagging commits with what type of improvement it is, and/or using semantic commit messages\)
  * [ ] Showing feature addition
  * [ ] Showing improvements made as a result of testing
  * [ ] Marking commits as minor when features are rough/the unpolished product \(before the feature is complete\)
  * [ ] Black box testing \(getting someone without knowledge of the code, to test the project, throughout the development even where it seems unnecessary, to conform to the requirements of the project\)
   * [ ] Perhaps look at using Jetbrains' local TMS or the 'behave' Python tool to make this more trackable 
  * [ ] White box testing \(just me testing parts of code as they're added\)
* [ ] Relevant implications \(finish off this whole list\)
* [ ] Shown concept, as in, a demo of the final product
* [ ] Evidence of designation and considered implications of selected structure \(just one thick docstring in my database logic class should do it\), but also of the language/s
* [ ] Evidence of data integrity/testing procedures \(making sure SQL injection can't happen, and invalid, malformed, or otherwise malicious data is sanitised and/or rejected\)
* [ ] Evidence of queries \(either by quote or by screenshot should be fine, and I can just comment a method or an instance of the method\)
* [ ] Evidence of customized data displays \(a subset of data and data sorting should do this, as well as showing the data in different formats\)
* [ ] Showing that the database is dynamically linked to the display \(similar to how I used Jinja2 in [AS91892](https://github.com/CyberFlameGO/AS91892) last year\)
* [ ] Showing data access \- not too sure how I'll do this but I might restrict access in the code instead of on the database framework
* [ ] Showing the use of multiple tables (relational)

* [ ] Showing use of tools and techniques \(tools can just be deps and IDE, and I don't really know for techniques but this can be re\-looked at later \- I believe the evidence will present itself as the project develops\)
* [ ] Comments/documentation \(docstrings, schema if appropriate, etc.\)
  * [ ] Schema \(with iterative improvement somehow?\) \(the native DBMS one can be used but only to complement a provided database structure design\) + data dictionary *\(a good idea is to use a Mermaid diagram so it's visualisable\)* 
* [ ] Testing \(see iterative improvement proof\)
* [ ] Following conventions of language
* [ ] "Complex techniques" \(as defined by the AS91906 spec\)
* [ ] Debugging \(code coverage I guess, links into testing\)
* [ ] Store images in base64 in the database
* [ ] For teacher emails use a regex to check if it's a valid teacher email and also filter domain
* [ ] Prior to submitting the internal, pin all versions of dependencies in `requirements.txt`.
* [ ] Use a TOML file for strings and refer to strings in the code using the TOML file instead of hardcoding them into the program \(use tomllib for parsing\).
* [x] Use Sentry for error reporting and finding errors during testing between each commit. 
* [ ] Create a linter workflow and a unit test \(perhaps fuzz program too\) to run on each push to the repo

##### General to\-do
* [x] Finish repo config \(pull off of AS91896 and AS91892 config files\) - merging of the repo-setup/init branch is not contingent on this
* [x] Add .gitignore

##### Notes
* [ ] Adapt database wrapper to be more flexible in terms of CRUD operations and checking
* [ ] Potentially look into using a different database framework
* [ ] Perhaps make this project rely on queries for reusability \(make a super simple API and just make the webpages send requests to the API, instead of making the webpage routes contain the code to run if that makes sense\)
* [ ] GitHub Projects may be a good way to organise what I have to do
* [ ] For the audit log part of the program (see Google Sheets as that is the layout), create a table which has an `id` field and a field which is of `blob` type, and whenever an auditable action takes place, store the relevant information in an object which gets serialised and stored in that blob field, and in the main table, for the `auditableActivities` field, if a word is updated/created (as in, if the auditable activity is related to a word), update the row to refer to the audit log table (so create the audit log row first, and update the `auditableActivities` field to refer to that audit log row.
* [ ] \-
