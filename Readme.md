Math Wiki (2019)
============
Aaron Smith:  ams3878@rit.edu
Grant Larsen: gl9191@rit.edu
Description:
---------------
App that queries the Math Tagged wikipedia Corpus.
Imporant Files:
---------------
mysite/
>mathIR/
>>custom_lib/
>>>All alogorithms used for querying and displaying information

>>static/
>>>idexTSV/
>>>>All .tsv used for indexing 
>>>collectionDocsTSV/html
>>>>the html files that have valid filenames
>>>mathIR/MathTagArticles
>>>>All tar files
>>templates/home/
>>>html that displays the user interface (home.html, results.html)

>>views.py
>>>results function is the __main__ of the app

Any directory of file not listed is relevenat only to the functioning of django.

Framework:
---------------------
This app uses the Django framework in order to handle the webserver,
render python code to html, and http requests.

Installation:
-------------------------------
If Django is not [installed](https://docs.djangoproject.com/en/2.2/intro/install/)

The nltk lib should be included in the files but if not...[click here](https://www.nltk.org/install.html)

Once Django is ready navigate to the IR_p2 directory
it should be the top level from the source.zip
Use the following cmd to start the webserver:

python manage.py runserver

This will start a webserver of the Pony Portal app on the local host.

From there all interaction will be done from a browser starting at….
[http://127.0.0.1:8000/ponyportal/](http://127.0.0.1:8000/math/)

