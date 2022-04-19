
##Taxonomic Guide app

Proof of concept, exchange format example and validator and application data model.

What's missing for the final app:
- Users with permissions.
- Persistency mechanism for both management data and the cards themselves.
- Client-side card editor.
- User & dev docs.
- ...

This app should work out-of-the-box with python 3.8, provided that `requirements.txt` is installed.

Url for viewing the main example is: http://localhost:5005/static/ok_example.html

**Note**: Some Webkit bugs affect the rendering of cards in Safari:

https://bugs.webkit.org/show_bug.cgi?id=77803

https://bugs.webkit.org/show_bug.cgi?id=160137

https://bugs.webkit.org/show_bug.cgi?id=208441

https://bugs.webkit.org/show_bug.cgi?id=215659

https://bugs.webkit.org/show_bug.cgi?id=139322

https://bugs.webkit.org/show_bug.cgi?id=114579

The result is that low-res images are decorated with (relatively) thick circled numbers and arrow ends.