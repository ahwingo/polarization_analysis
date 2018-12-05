#---------------------------------------------------------------
#---------------------------------------------------------------
# Setting Up GUI.
#---------------------------------------------------------------
#---------------------------------------------------------------

# Loading modules for GUI
import tkinter
from tkinter import *
from tkinter.ttk import *
import cv2
import PIL.Image, PIL.ImageTk

# Creating the window.
window = Tk() 
window.title("MEDIA BIAS ANALYSIS DEMO")
window.geometry('600x700')

# Loading the background.
cv_img = cv2.cvtColor(cv2.imread("gui_background_mod.jpg"), cv2.COLOR_BGR2RGB)
height, width, no_channels = cv_img.shape
canvas = tkinter.Canvas(window, width = width, height = height)
canvas.place(x=0, y=0, relwidth=1, relheight=1)
photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(cv_img))
canvas.create_image(0, 0, image=photo, anchor=tkinter.NW)

# Label for the article title
headline_lbl = Label(window, text="", font="Helvetica 14 bold", wraplength=500)
headline_lbl.place(relx=0.5, y=70, anchor=CENTER)

# Label for the sentence which contributed most to the articles sentiment score
max_sent_lbl = Label(window, text="", font="Helvetica 14 italic", wraplength=500)
max_sent_lbl.place(relx=0.5, y=130, anchor=CENTER)

# Lists containing dots currently on the screen, and their associated values.
dots_on_screen = []
values_for_dots_on_screen = []

# Function to clear the screen of all dots.
def clear_dots():

	global dots_on_screen
	global headline_lbl
	global max_sent_lbl
	global values_for_dots_on_screen

	# RESET SCREEN TO DEFAULTS
	for dot in dots_on_screen:
		canvas.delete(dot)
	dots_on_screen = []
	headline_lbl.configure(text="")
	max_sent_lbl.configure(text="")
	values_for_dots_on_screen = []


#---------------------------------------------------------------


#---------------------------------------------------------------
#---------------------------------------------------------------
# Loading The Database
#---------------------------------------------------------------
#---------------------------------------------------------------

import sqlite3

conn = sqlite3.connect('media_bias_demo_mod.db')
c = conn.cursor()

#---------------------------------------------------------------



#---------------------------------------------------------------
#---------------------------------------------------------------
# Using The DB To Populate The List Of Topics
#---------------------------------------------------------------
#---------------------------------------------------------------

# GOAL: Select the Top 100 topics (topics mentioned the most)
# Want to group topic_mentions by t_id, then get count(*) AS num_mentions and t_id. Then, join that with topic on t_id, and order by num_mentions, finally taking t_id and phrase.
exc_stmt = """SELECT t.Phrase FROM Topic AS t, Topic_Mention AS tm WHERE t.T_ID == tm.T_ID GROUP BY t.Phrase ORDER BY COUNT(*) DESC"""
c.execute(exc_stmt)
list_of_topics = c.fetchmany(100)

MAX_NUM_OF_TOPICS_TO_INCLUDE = 100

all_topics = []
count_of_topics_from_list = 0
for topic in list_of_topics:
	fixed_topic = str(topic).strip("{")
	fixed_topic = str(fixed_topic).strip("}")
	fixed_topic = str(fixed_topic).strip("('")
	fixed_topic = str(fixed_topic).strip("'),")

	if count_of_topics_from_list > (MAX_NUM_OF_TOPICS_TO_INCLUDE - 1):
		break
	all_topics.append(fixed_topic)
	count_of_topics_from_list += 1

# Sort topics alphabetically
all_topics = sorted(all_topics, key=str.lower)

#---------------------------------------------------------------



#---------------------------------------------------------------
#---------------------------------------------------------------
# Load information for the dot (article) clicked.
#---------------------------------------------------------------
#---------------------------------------------------------------

def on_object_click(event):

	# Process and clean the buttons tag.
	the_tag = canvas.gettags(event.widget.find_withtag("current"))[0]
	values_index = int(the_tag)

	# Update the labels for headline and sentence.
	headline = values_for_dots_on_screen[values_index][1]
	sentence = values_for_dots_on_screen[values_index][3]
	sentence = sentence.replace("  ", " ")
	sentence = sentence + "..."
	headline_lbl.configure(text=headline)
	max_sent_lbl.configure(text=sentence)
	
#---------------------------------------------------------------




#---------------------------------------------------------------
#---------------------------------------------------------------
# This function is called when a new topic is selected.
#---------------------------------------------------------------
#---------------------------------------------------------------

import numpy as np 
import math

def show_articles_for_topic(event):

	# Clear the screen.
	clear_dots()

	dflt_color = "#000000"
	nyt_color = "#21e45e"
	fox_color = "#e84f4f"

	global selected_date
	global dots_on_screen


	# GET CURRENTLY SELECTED TOPIC
	the_topic_selected = combo.get()


	# GOAL: Find all articles (A_ID, Headline, Date_Published, P_Link, Overall_S_Score, J_ID, P_ID) that mention the selected topic.
	# STEP 1: Find all Topic_Mentions that HAVE T_ID == all_topics[the_topic_selected], and get its A_ID
	# STEP 2: Find all Articles included in that list of topic mentions
	
	exc_stmt = """SELECT * FROM Article AS a, Topic_Mention AS tm, Topic AS t """
	exc_stmt = exc_stmt + """WHERE a.A_ID == tm.A_ID AND tm.T_ID == t.T_ID AND t.Phrase == :phs GROUP BY Headline ORDER BY Overall_Score"""
	c.execute(exc_stmt, {"phs": the_topic_selected})

	# Format of the tuple returned = (A_ID, Headline, Date_Published, P_Link, Overall_S_Score, J_ID, P_ID, TM_ID, T_ID, Max_Content, Overall_Score)
	list_of_relevant_articles = c.fetchall()

	a_count = 0
	for article_tuple in list_of_relevant_articles:

		a_headline = article_tuple[1]
		a_date = article_tuple[2]
		a_link = article_tuple[3]
		a_overall_score = article_tuple[4]
		a_paper = article_tuple[6]
		a_max_context = article_tuple[9]
		a_overall_score = article_tuple[10]

		the_color = dflt_color
		if a_paper == "The New York Times":
			the_color = nyt_color
		elif a_paper == "Fox News":
			the_color = fox_color

		x_range = len(list_of_relevant_articles) + 1
		px = 116 + 344*(a_count + 1)/x_range

		# Normalize the score using tanh to get values between 1 and -1
		# Negate the score to account for GUI coordinate system (more negative articles should have higher y pos) 
		normalized_score_tanh = np.tanh(a_overall_score)
		negated_score = normalized_score_tanh*(-1)
		py = 294 + 60*negated_score

		# Create a dot for this article.	
		dot_radius = 4
		x1, y1 = (px - dot_radius), (py - dot_radius)
		x2, y2 = (px + dot_radius), (py + dot_radius)



		
		# Create tuple that holds the values for this dot, and append tuple to the list.
		tup_for_dot = (a_link, a_headline, a_paper, a_max_context)
		values_for_dots_on_screen.append(tup_for_dot)


		# Create and add the dot to the screen. Its tag is the index of its values.
		the_dot = canvas.create_oval(x1, y1, x2, y2, fill=the_color, tags=str(a_count))
		canvas.itemconfig(the_dot, fill=the_color)
		dots_on_screen.append(the_dot)
		canvas.tag_bind(the_dot, '<Button-1>', on_object_click)  

		# Increment the article count.
		a_count += 1


"""
		# Create a value you can pass as a tag.	
		a_headline_passable = a_headline.replace(" ", "_")
		a_paper_passable = a_paper.replace(" ", "_")
		a_max_context_passable = a_max_context.replace(" ", "_")
	
		thing_to_pass_as_tag = a_link + "---SPLIT-ON-ME---" + a_headline_passable
		thing_to_pass_as_tag = thing_to_pass_as_tag + "---SPLIT-ON-ME---" + a_paper_passable
		thing_to_pass_as_tag = thing_to_pass_as_tag + "---SPLIT-ON-ME---" + a_max_context_passable

		the_dot = canvas.create_oval(x1, y1, x2, y2, fill=the_color, tags=thing_to_pass_as_tag)
		
		canvas.itemconfig(the_dot, fill=the_color)
		dots_on_screen.append(the_dot)
		canvas.tag_bind(the_dot, '<Button-1>', on_object_click)  

		a_count += 1
"""

#--------------------------------------------------------------------------------



#---------------------------------------------------------------
#---------------------------------------------------------------
# Adding a topics dropdown box.
#---------------------------------------------------------------
#---------------------------------------------------------------

combo_topics = ()
combo = Combobox(window, width=25)
combo.bind("<<ComboboxSelected>>", show_articles_for_topic)
combo.place(relx=0.5, y=30, anchor=CENTER)
combo.config(state="readonly")
for topic in all_topics:
	combo_topics = combo_topics + (topic,)
combo['values']= combo_topics
combo.current(0)

#---------------------------------------------------------------



#---------------------------------------------------------------
#---------------------------------------------------------------
# Calling GUI Window.
#---------------------------------------------------------------
#---------------------------------------------------------------

window.mainloop()

#---------------------------------------------------------------
