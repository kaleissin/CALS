============
Data Sources
============

This all started with a book::

    A dictionary of grammatical terms in linguistics by Carl Darling Buck, 
    published by The University of Chicago Press in 1949.

... hereafter known as The Book.

Looking for a digital version of The Book lead to IDS and WOLD and a
desire to see how much overlap there was with the various shorter
universal wordlists like Swadesh.

There is no digital version of the words in The Book here, as they were
"generated" by cloning the IDS-list and manually going through each
meaning in The Book and the IDS-list looking for differences. Not a
batchable operation. That list was then matched with the WOLD list,
looking up and comparing number and meaning, and *that* list was used as
a basis to blend in the shorter lists.

The final conglomeration no doubt contains errors.

How to regenerate the sources
-----------------------------

swadesh, yakhontov, holman

    http://en.wikipedia.org/wiki/Swadesh_list

buck-categories

    Copied from IDS then hand checked against the book

ids.tab

    http://lingweb.eva.mpg.de/ids/

    #. Click on "Download Data"
    #. Choose 
        
        - Entry id: 1.11
        - Entry Translations: English
        - IDS Chapters: all chapters
    #. Click "Download Result"

    Results in nice tab-separated file

wold.html

    http://wold.livingsources.org/meaning

    Scrape the resultant HTML for the actual code-meaning pairs

23-24.tab

    Words and categories unique to WOLD

    This is an extract from the result of the previous process
