# Recommendation engine for Placedumarche.com
Python flask web.app deployed in Heroku for collect user input and recommend food security organizations in Montreal  


Based on Machine Learning Deployment Tutorials by Abhinav Sagar  
https://github.com/abhinavsagar/Machine-Learning-Deployment-Tutorials


## 1. How to deploy on Heroku
Visit Heroku website and follow the instructions for "Getting Started on Heroku with Python"
https://devcenter.heroku.com/articles/getting-started-with-python

The steps, broadly, are:  
1. Install Heroku  
2. Clone this repository  
3. Deploy the app  

## 2. Embed the web app as an iFrame in WordPress
1. On the page editor, add a shortcode block  
2. Enter the shortcode:  
[iframe src='url_for_heroku_app']  
3. replace url_for_heroku_app by the full link for your hero app. ex:  
[iframe src="https://secure-sierra-51423.herokuapp.com/"]

## License

```
MIT License

Copyright (c) 2020 Francis McGuire

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
