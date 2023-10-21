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
	* [ ] White box testing \(just me testing parts of code as they're added\)
* [ ] Relevant implications \(finish off this whole list\)
* [ ] Shown concept, as in, a demo of the final product
* [x] Evidence of designation and considered implications of selected structure \(just one thick docstring in my database logic class should do it\), but also of the language/s
* [x] Evidence of data integrity/testing procedures \(making sure SQL injection can't happen, and invalid, malformed, or otherwise malicious data is sanitised and/or rejected\)
* [x] Evidence of queries \(either by quote or by screenshot should be fine, and I can just comment a method or an instance of the method\)
* [x] Evidence of customized data displays \(a subset of data and data sorting should do this, as well as showing the data in different formats\)
* [x] Showing that the database is dynamically linked to the display \(similar to how I used Jinja2 in [AS91892](https://github.com/CyberFlameGO/AS91892) last year\)
* [x] Showing the use of multiple tables (relational)

* [ ] Showing use of tools and techniques \(tools can just be deps and IDE, and I don't really know for techniques but this can be re\-looked at later \- I believe the evidence will present itself as the project develops\)
* [ ] Comments/documentation \(docstrings, schema if appropriate, etc.\)
	* [ ] Schema \(with iterative improvement somehow?\) \(the native DBMS one can be used but only to complement a provided database structure design\) + data dictionary *\(a good idea is to use a Mermaid diagram so it's visualisable\)*
* [ ] Testing \(see iterative improvement proof\)
* [ ] Following conventions of language
* [ ] "Complex techniques" \(as defined by the AS91906 spec\)
* [ ] Debugging \(code coverage I guess, links into testing\)
* [x] Use Sentry for error reporting and finding errors during testing between each commit.

##### General to\-do

* [x] Finish repo config \(pull off of AS91896 and AS91892 config files\) - merging of the repo-setup/init branch is not contingent on this
* [x] Add .gitignore

##### Notes

* [x] Adapt database wrapper to be more flexible in terms of CRUD operations and checking
* [x] Potentially look into using a different database framework (done - used SQLAlchemy)
* [ ] GitHub Projects may be a good way to organise what I have to do

---
Diagram

```mermaid
```
