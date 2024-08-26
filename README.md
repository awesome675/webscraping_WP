<h1>Article -> WordPress Post</h1>

<p>This automation gathers articles from a variety of sources and posts them to a WordPress site, daily.</p>

<h2>Tools Used</h2>
<ul>
  <li><strong>Python:</strong> Used to make the actual script, handling logic of gathering (web scraping), scraping, and storing articles in a .txt file (not SQL database, keeping it simple). Uses wordpress_xmlrpc package to post them to wordpress site</li>
  <li><strong>JSON:</strong> The JSON file is used to store the sources and their selectors to dynamically handle web scraping</li>
  <li><strong>Batch File:</strong> Used to automate posting on a daily basis using Windows Task Scheduler</li>
</ul>


