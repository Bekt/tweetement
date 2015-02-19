## Tweetement
TODO: Write me.

Live: http://tweetement.com/ (or http://tweetement0.appspot.com/)

## Development
### Requirements
* [Python 2.7](https://www.python.org/downloads/) and [pip](https://pip.pypa.io/en/latest/installing.html)
* [Google App Engine (GAE) SDK for
  Python](https://cloud.google.com/appengine/downloads)

### Setup
```bash
git clone git@github.com:Bekt/tweetement.git
cd tweetement
pip install -t lib/pip/ -r requirements.txt
```

### Get Twitter Access Tokens
* Follow instructions in `credentials.txt`.

### Run Locally
At this point, everything should be ready to go. To run the web service
locally:
```bash
# From project root.
<path-to-gae-sdk>/dev_appserver.py .
```

The service should be running at http://localhost:8080

You also should seed the list of stop words into your local datastore.
You only need to perform this once. Go to http://localhost:8000/console and execute:
```py
import seeds

seeds.seed_stopwords()
```

Make sure the entries have been entered at:
http://localhost:8000/datastore

### Frontend
* The frontend is written in [AngularJS](https://angularjs.org/) +
  [Bootstrap](http://getbootstrap.com/).
* See `index.html` and `assets/`.

### Backend
High overview of the flow:
* User submits a query via `enqueue()`.
* `enqueue()` creates a `Query` model and puts it in a queue (background
  job).
* The `Query` is popped from the queue (`tqueue.pop()`), `ExpandedQuery` is
  created and query expansion is performed (`tqueue.expand_query()`) by
calling Twitter Search API multiple times.

## License
TODO: Figure out what is an appropriate license type for this project.
