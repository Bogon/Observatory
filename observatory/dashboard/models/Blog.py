# Copyright (c) 2010, Nate Stedman <natesm@gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import datetime
from dashboard.util import find_author
from django.db import models
from lib import feedparser, dateutil
from EventSet import EventSet

# a blog for a project
class Blog(EventSet):
  class Meta:
    app_label = 'dashboard'
  
  # link to the blog, if it isn't hosted on dashboard
  url = models.URLField("Blog Web Address", max_length = 64)
  rss = models.URLField("Blog Feed", max_length = 64)
  
  # fetches the posts from the rss feed
  def fetch(self):
    import BlogPost
    
    # don't fetch internally hosted blogs
    if not self.from_feed: return
    
    events = []
    
    # parse and iterate the feed
    entries = feedparser.parse(self.rss).entries
    for post in entries:
      try:
        date = dateutil.parser.parse(post.date).replace(tzinfo=None)
      except:
        date = datetime.datetime.utcnow()
      
      # don't re-add old posts
      if self.most_recent_date >= date:
        continue
      
      try:
        content = post.content[0].value
      except:
        content = post.description
      
      try:
        author_name = post.author_detail["name"]
      except:
        author_name = None
      
      events.append(self.add_event(BlogPost.BlogPost,
        title = post.title,
        summary = post.description,
        from_feed = True,
        author_name = author_name,
        date = date,
        extra_args = {
          "external_link": post.link,
          "content": content,
          "blog_id": self.id
        }
      ))
    
    # find the new most recent date
    dates = [event.date for event in events if event is not None]
    dates.append(self.most_recent_date)
    self.most_recent_date = max(dates)
    self.save()