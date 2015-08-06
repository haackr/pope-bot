"""
Pope-Bot by /u/ryguyrun

Replies to posts with "TIL the Pope is Catholic"
if "Pope Francis" is in the title of the post.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License v2 as published by
the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

"""
import praw
import time
import cPickle
import os
import redis

ADMIN_USER = "ryguyrun"
USERAGENT = "Pope-Bot v1.0 by /u/ryguyrun"
#Bot will check these subreddits only.
SUBREDDITS = ["sidehugs", "brokehugs", "popebot"]
USERNAME = os.environ.get("REDDIT_USER")
PASSWORD = os.environ.get("REDDIT_PASS")
COMPLETED_POSTS_KEY = "complete:posts"

r = praw.Reddit(USERAGENT)
rd = redis.from_url(os.environ.get("REDIS_URL"))
completed_posts = []

def main():
	print(USERAGENT)
	r.login(USERNAME,PASSWORD,disable_warning=True)

	if rd.exists(COMPLETED_POSTS_KEY):
		loadCompleted()
		print "Read in from redis"

	while True:
		for sub in SUBREDDITS:
			subreddit = r.get_subreddit(sub)
			checkForFrancis(subreddit)
		checkForMessages()
		saveCompleted()
		time.sleep(900)

#check for post containing "Pope Francis" in the title, comment on them, and notify admin that comment has been made
def checkForFrancis(subreddit):
		for submission in subreddit.get_new(limit=30):
			if submission.id not in completed_posts and "pope francis" in submission.title.lower():
				try:
					submission.add_comment("TIL the Pope is Catholic")
				except praw.errors.RateLimitExceeded as e:
					print "Rate limit exceeded while commenting... Waiting ", "%.2f" % e.sleep_time
					time.sleep(e.sleep_time)
				except praw.errors.HTTPException as e:
					print "HTTP Exception occured while trying to comment"
					print e;
				else:
					completed_posts.append(submission.id)
					print submission.id + ": " + submission.title
					r.send_message(ADMIN_USER, "pope-bot commented ", submission.short_link)

#Check for messages and notify of any recieved
def checkForMessages():
	unreadMessages = r.get_unread(unset_has_mail=True, update_user=True)
	for msg in unreadMessages:
		try:
			r.send_message(ADMIN_USER, 'Message Sent To pope-bot', messageNotificationBuilder(msg))
		except praw.errors.HTTPException as e:
			print "HTTP Exception occured while trying to send message notification"
		except praw.errors.RateLimitExceeded as e:
			print "Rate Limit Exceeded while trying to send message notification. Waiting ", "%.2f" % e.sleep_time
			time.sleep(e.sleep_time)
		else:
			msg.mark_as_read()
			print "Messgae notification sent."

#Builds the message text for checkForMessgages()
def messageNotificationBuilder(message):
	username = message.author.name
	contextUrlFragment = message.context
	isCommentReply = message.was_comment
	subject = message.subject
	body = message.body
	replyString = "**Subject: " + subject + "**\n\n" + body + "\n\n---\n\n**From: /u/" + username + "**"
	if isCommentReply:
		replyString = replyString + "\n\n[reddit.com" + contextUrlFragment + "](http://reddit.com" + contextUrlFragment + ")"
	return replyString


#Writes the completed posts to redis database.
def saveCompleted():
	print "Writing to database..."
	rd.set(COMPLETED_POSTS_KEY,cPickle.dumps(completed_posts))
	print "Complete."

#Gets the completed posts from redis database.
def loadCompleted():
	global completed_posts
	completed_posts = (cPickle.loads(rd.get(COMPLETED_POSTS_KEY)))
	print completed_posts

if __name__ == '__main__': main()
