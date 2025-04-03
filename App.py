###### Packages Used ######
import streamlit as st # core package used in this project
import pandas as pd
import base64, random
import time,datetime
import pymysql
import os
import socket
import platform
#import geocoder
import secrets
import io,random
import plotly.express as px # to create visualisations at the admin session
import plotly.graph_objects as go
#from geopy.geocoders import Nominatim
# libraries used to parse the pdf files
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
from streamlit_tags import st_tags
from PIL import Image
import difflib
# pre stored data for prediction purposes
from Courses import ds_course,web_course,android_course,ios_course,uiux_course,resume_videos,interview_videos
import nltk
nltk.download('stopwords')
# Add this near the top of your imports
import spacy
try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    print('Downloading language model for the spaCy NLP library\n'
        "(don't worry, this will only happen once)")
    from spacy.cli import download
    download('en_core_web_sm')
    nlp = spacy.load('en_core_web_sm')

import re
from spacy.matcher import Matcher
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

###### Preprocessing functions ######


# Generates a link allowing the data in a given panda dataframe to be downloaded in csv format 
def get_csv_download_link(df,filename,text):
    csv = df.to_csv(index=False)
    ## bytes conversions
    b64 = base64.b64encode(csv.encode()).decode()      
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


# Reads Pdf file and check_extractable
def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()

    ## close open handles
    converter.close()
    fake_file_handle.close()
    return text


# show uploaded file path to view pdf_display
def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


# course recommendations which has data already loaded from Courses.py
def course_recommender(course_list):
    st.subheader("**Courses & Certificates Recommendations 👨‍🎓**")
    c = 0
    rec_course = []
    ## slider to choose from range 1-10
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 5)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course


###### Database Stuffs ######

    
# sql connector
connection = pymysql.connect(host='localhost',user='root',password='Ehusei3opqaj293@$uwi',db='cv')
cursor = connection.cursor()


# inserting miscellaneous data, fetched results, prediction and recommendation into user_data table
def insert_data(sec_token,ip_add,host_name,dev_user,os_name_ver,act_name,act_mail,act_mob,name,email,res_score,timestamp,no_of_pages,reco_field,cand_level,skills,recommended_skills,courses,pdf_name):
    DB_table_name = 'user_data'
    insert_sql = f"INSERT INTO {DB_table_name} VALUES (0, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    rec_values = (str(sec_token),str(ip_add),host_name,dev_user,os_name_ver,act_name,act_mail,act_mob,name,email,str(res_score),timestamp,str(no_of_pages),reco_field,cand_level,skills,recommended_skills,courses,pdf_name)
    cursor.execute(insert_sql, rec_values)
    connection.commit()


# inserting feedback data into user_feedback table
def insertf_data(feed_name,feed_email,feed_score,comments,Timestamp):
    DBf_table_name = 'user_feedback'
    insertfeed_sql = "insert into " + DBf_table_name + """
    values (0,%s,%s,%s,%s,%s)"""
    rec_values = (feed_name, feed_email, feed_score, comments, Timestamp)
    cursor.execute(insertfeed_sql, rec_values)
    connection.commit()


###### Setting Page Configuration (favicon, Logo, Title) ######


st.set_page_config(
   page_title="AI Resume Analyzer",
   page_icon='./Logo/recommend.png',
)

# Define SKILLS_DB at the module level (top of file)
SKILLS_DB = {
    'technical': {
        'programming': [
            'python', 'java', 'c++', 'ruby', 'javascript', 'php', 'swift', 'r programming',
            'scala', 'golang', 'typescript', 'kotlin', 'rust', 'matlab'
        ],
        'web_dev': [
            'html', 'css', 'react', 'angular', 'node.js', 'vue.js', 'django', 'flask',
            'bootstrap', 'jquery', 'sass', 'less', 'webpack', 'redux', 'graphql'
        ],
        'databases': [
            'sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'redis', 'elasticsearch',
            'dynamodb', 'cassandra', 'firebase'
        ],
        'cloud_devops': [
            'git', 'docker', 'kubernetes', 'jenkins', 'aws', 'azure', 'gcp', 'terraform',
            'ansible', 'ci/cd', 'nginx', 'linux'
        ],
        'ai_ml': [
            'tensorflow', 'pytorch', 'scikit-learn', 'machine learning', 'deep learning',
            'nlp', 'computer vision', 'data analysis', 'pandas', 'numpy', 'scipy'
        ],
        'design': [
            'photoshop', 'illustrator', 'figma', 'sketch', 'adobe xd', 'indesign',
            'after effects', 'premiere pro', 'ui/ux', 'responsive design'
        ]
    },
    'soft': [
        'leadership', 'communication', 'problem solving', 'team work', 'time management',
        'project management', 'analytical', 'strategic thinking', 'detail oriented',
        'agile', 'scrum', 'critical thinking', 'presentation', 'negotiation'
    ]
}

###### Main function run() ######

def extract_text_from_pdf(file_path):
    """Extract text from PDF using pdfminer"""
    return pdf_reader(file_path)

def extract_name(nlp_text, matcher):
    """Extract name from text using spaCy"""
    pattern = [{'POS': 'PROPN'}, {'POS': 'PROPN'}]
    matcher.add('NAME', [pattern])
    matches = matcher(nlp_text)
    
    for match_id, start, end in matches:
        span = nlp_text[start:end]
        return span.text
    return None

def extract_email(text):
    """Extract email from text using regex"""
    email = re.findall(r"([^@|\s]+@[^@]+\.[^@|\s]+)", text)
    if email:
        try:
            return email[0].split()[0].strip(';')
        except IndexError:
            return None

def extract_mobile_number(text):
    """Extract mobile number from text using regex"""
    phone = re.findall(re.compile(r'(?:(?:\+?([1-9]|[0-9][0-9]|[0-9][0-9][0-9])\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([0-9][1-9]|[0-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?'), text)
    if phone:
        number = ''.join(phone[0])
        if len(number) > 10:
            return '+' + number
        return number

def extract_skills(text, noun_chunks):
    """Extract skills from text using spaCy"""
    skills = []
    
    # Process text with spaCy
    doc = nlp(text.text.lower() if hasattr(text, 'text') else text.lower())
    
    # Initialize containers for skills
    categorized_skills = {
        'programming': [],
        'web_dev': [],
        'databases': [], 
        'cloud_devops': [],
        'ai_ml': [],
        'design': [],
        'soft_skills': [],
        'technical_term': []
    }
    
    # Check for skills matches in each category
    for category, skill_list in SKILLS_DB['technical'].items():
        for skill in skill_list:
            if skill.lower() in doc.text:
                categorized_skills[category].append(skill)
                skills.append((skill, category))
                
    # Check soft skills
    for skill in SKILLS_DB['soft']:
        if skill.lower() in doc.text:
            categorized_skills['soft_skills'].append(skill) 
            skills.append((skill, 'soft_skills'))
            
    # Process noun chunks for additional technical terms
    for chunk in noun_chunks:
        token = chunk.text.lower().strip()
        tech_indicators = ['api', 'sdk', 'framework', 'library', 'database', 'language']
        if (len(token) > 2 and 
            not any(char.isdigit() for char in token) and
            any(indicator in token for indicator in tech_indicators)):
            
            categorized_skills['technical_term'].append(token)
            skills.append((token, 'technical_term'))
            
    return {
        'all_skills': [s[0] for s in skills],
        'categorized': categorized_skills
    }


def parse_resume(file_path):
    """Custom resume parser"""
    matcher = Matcher(nlp.vocab)
    
    # Extract text from PDF
    text = extract_text_from_pdf(file_path)
    
    # Process text with spaCy
    doc = nlp(text)
    
    # Extract information
    name = extract_name(doc, matcher)
    email = extract_email(text)
    mobile_number = extract_mobile_number(text)
    
    # Extract skills using noun chunks
    skills_data = extract_skills(text, list(doc.noun_chunks))
    skills = skills_data['all_skills']
    
    # Count pages
    with open(file_path, 'rb') as fh:
        no_of_pages = len(list(PDFPage.get_pages(fh)))
    
    return {
        'name': name,
        'email': email, 
        'mobile_number': mobile_number,
        'skills': skills,
        'no_of_pages': no_of_pages
    }

def run():
    

    st.sidebar.markdown("# Choose Something...")
    activities = ["User", "Feedback", "About", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    link = '<b>Built by <a href="https://github.com/ShadowAniket" style="text-decoration: none; color: #021659;">Aniket</a></b>' 
    st.sidebar.markdown(link, unsafe_allow_html=True)
    st.sidebar.markdown('''
        <!-- site visitors -->

        <div id="sfct2xghr8ak6lfqt3kgru233378jya38dy" hidden></div>

        <noscript>
            <a href="https://www.freecounterstat.com" title="hit counter">
                <img src="https://counter9.stat.ovh/private/freecounterstat.php?c=t2xghr8ak6lfqt3kgru233378jya38dy" border="0" title="hit counter" alt="hit counter"> -->
            </a>
        </noscript>
    
        <p>Visitors <img src="https://counter9.stat.ovh/private/freecounterstat.php?c=t2xghr8ak6lfqt3kgru233378jya38dy" title="Free Counter" Alt="web counter" width="60px"  border="0" /></p>
    
    ''', unsafe_allow_html=True)

    ###### Creating Database and Table ######


    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS CV;"""
    cursor.execute(db_sql)


    # Create table user_data and user_feedback
    DB_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                    sec_token varchar(20) NOT NULL,
                    ip_add varchar(50) NULL,
                    host_name varchar(50) NULL,
                    dev_user varchar(50) NULL,
                    os_name_ver varchar(50) NULL,
                    latlong varchar(50) NULL,
                    city varchar(50) NULL,
                    state varchar(50) NULL,
                    country varchar(50) NULL,
                    act_name varchar(50) NOT NULL,
                    act_mail varchar(50) NOT NULL,
                    act_mob varchar(20) NOT NULL,
                    Name varchar(500) NOT NULL,
                    Email_ID VARCHAR(500) NOT NULL,
                    resume_score VARCHAR(8) NOT NULL,
                    Timestamp VARCHAR(50) NOT NULL,
                    Page_no VARCHAR(5) NOT NULL,
                    Predicted_Field BLOB NOT NULL,
                    User_level BLOB NOT NULL,
                    Actual_skills BLOB NOT NULL,
                    Recommended_skills BLOB NOT NULL,
                    Recommended_courses BLOB NOT NULL,
                    pdf_name varchar(50) NOT NULL,
                    PRIMARY KEY (ID)
                    );
                """
    cursor.execute(table_sql)


    DBf_table_name = 'user_feedback'
    tablef_sql = "CREATE TABLE IF NOT EXISTS " + DBf_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                        feed_name varchar(50) NOT NULL,
                        feed_email VARCHAR(50) NOT NULL,
                        feed_score VARCHAR(5) NOT NULL,
                        comments VARCHAR(100) NULL,
                        Timestamp VARCHAR(50) NOT NULL,
                        PRIMARY KEY (ID)
                    );
                """
    cursor.execute(tablef_sql)


    ###### CODE FOR CLIENT SIDE (USER) ######

    if choice == 'User':
        
        # Collecting Miscellaneous Information
        act_name = st.text_input('Name*')
        act_mail = st.text_input('Mail*')
        act_mob  = st.text_input('Mobile Number*')
        sec_token = secrets.token_urlsafe(12)
        host_name = socket.gethostname()
        ip_add = socket.gethostbyname(host_name)
        dev_user = os.getlogin()
        os_name_ver = platform.system() + " " + platform.release()


        # Upload Resume
        st.markdown('''<h5 style='text-align: left; color: #021659;'> Upload Your Resume, And Get Smart Recommendations</h5>''',unsafe_allow_html=True)
        
        ## file upload in pdf format
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            with st.spinner('Hang On While We Cook Magic For You...'):
                time.sleep(4)
        
            ### saving the uploaded resume to folder
            save_image_path = './Uploaded_Resumes/'+pdf_file.name
            pdf_name = pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)

            ### parsing and extracting whole resume 
            resume_data = parse_resume(save_image_path)  # Replace ResumeParser usage with this line
            if resume_data:
                
                ## Get the whole resume data into resume_text
                resume_text = pdf_reader(save_image_path)

                ## Showing Analyzed data from (resume_data)
                st.header("**Resume Analysis 🤘**")
                st.success("Hello "+ resume_data['name'])
                st.subheader("**Your Basic info 👀**")
                try:
                    st.text('Name: '+resume_data['name'])
                    st.text('Email: ' + resume_data['email'])
                    st.text('Contact: ' + resume_data['mobile_number'])
                    st.text('Resume pages: '+str(resume_data['no_of_pages']))

                except:
                    pass
                
                ## Predicting Candidate Experience Level 

                # Define keywords for each level
                internship_keywords = ['INTERNSHIP', 'INTERNSHIPS', 'Internship', 'Internships']
                experience_keywords = ['EXPERIENCE', 'WORK EXPERIENCE', 'Experience', 'Work Experience']

                # Initialize candidate level
                cand_level = ''

                # Check if the number of pages is less than 1 (Fresher level)
                if resume_data['no_of_pages'] < 1:
                    cand_level = "General"
                    st.markdown('<h4 style="text-align: left; color: #d73b5c;">You are at Fresher level!</h4>', unsafe_allow_html=True)

                # Check if any of the internship keywords are present (Intermediate level)
                elif any(keyword in resume_text for keyword in internship_keywords):
                    cand_level = "Intermediate"
                    st.markdown('<h4 style="text-align: left; color: #1ed760;">You are at intermediate level!</h4>', unsafe_allow_html=True)

                # Check if any of the experience keywords are present (Experienced level)
                elif any(keyword in resume_text for keyword in experience_keywords):
                    cand_level = "Experienced"
                    st.markdown('<h4 style="text-align: left; color: #fba171;">You are at experience level!</h4>', unsafe_allow_html=True)

                # Default to Fresher level if no other conditions are met
                else:
                    cand_level = "Fresher"
                ## Skills Analyzing and Recommendation
                st.subheader("**Skills Recommendation 💡**")

                # Get the text from PDF
                resume_text = pdf_reader(save_image_path)

                # Process resume text with spaCy
                doc = nlp(resume_text)

                ### Current Analyzed Skills
                if not isinstance(resume_data['skills'], list):
                    print("Warning: resume_data['skills'] is not a list!")
                    if isinstance(resume_data['skills'], str):
                        resume_data['skills'] = resume_data['skills'].split(",")  # Convert comma-separated string to list
                    else:
                        resume_data['skills'] = []  # Default to an empty list

                # Clean skills (remove spaces, avoid case issues)
                resume_data['skills'] = [skill.strip() for skill in resume_data['skills']]

                # Debugging: Print extracted skills
                print("Extracted Skills:", resume_data['skills'])

                keywords = st_tags(label='### Your Current Skills',
                    text='See our skills recommendation below', value=resume_data['skills'], key='1')

                ### Keywords for Recommendations
                ds_keyword = ['tensorflow', 'keras', 'pytorch', 'machine learning', 'deep learning', 'flask', 'streamlit']
                web_keyword = ['react', 'django', 'node js', 'react js', 'php', 'laravel', 'magento', 'wordpress', 'javascript', 'angular js', 'C#', 'Asp.net', 'flask']
                android_keyword = ['android', 'android development', 'flutter', 'kotlin', 'xml', 'kivy']
                ios_keyword = ['ios', 'ios development', 'swift', 'cocoa', 'cocoa touch', 'xcode']
                uiux_keyword = ['ux', 'adobe xd', 'figma', 'zeplin', 'balsamiq', 'ui', 'prototyping', 'wireframes', 'storyframes', 'adobe photoshop', 'photoshop', 'editing', 'adobe illustrator', 'illustrator', 'adobe after effects', 'after effects', 'adobe premier pro', 'premier pro', 'adobe indesign', 'indesign', 'wireframe', 'solid', 'grasp', 'user research', 'user experience']
                n_any = ['english', 'communication', 'writing', 'microsoft office', 'leadership', 'customer management', 'social media']

                ### Skill Recommendations Starts                
                recommended_skills = []
                reco_field = ''
                rec_course = ''

                ### Skill Matching Logic
                for skill in resume_data['skills']:
                    skill_cleaned = skill.strip().lower()  # Clean and lowercase for comparison

                    #### Data science recommendation
                    if skill_cleaned in ds_keyword:
                        print(f"✅ Matched: {skill} (Data Science)")
                        reco_field = 'Data Science'
                        st.success("** Our analysis says you are looking for Data Science Jobs.**")
                        recommended_skills = ['Data Visualization', 'Predictive Analysis', 'Statistical Modeling', 'Data Mining', 'Clustering & Classification', 'Data Analytics', 'Quantitative Analysis', 'Web Scraping', 'ML Algorithms', 'Keras', 'Pytorch', 'Probability', 'Scikit-learn', 'Tensorflow', "Flask", 'Streamlit']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                            text='Recommended skills generated from System', value=recommended_skills, key='2')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding these skills to your resume will boost 🚀 your chances of getting a Job</h5>''', unsafe_allow_html=True)
                        rec_course = course_recommender(ds_course)
                        break

                    #### Web development recommendation
                    elif skill_cleaned in web_keyword:
                        print(f"✅ Matched: {skill} (Web Development)")
                        reco_field = 'Web Development'
                        st.success("** Our analysis says you are looking for Web Development Jobs **")
                        recommended_skills = ['React', 'Django', 'Node JS', 'React JS', 'PHP', 'Laravel', 'Magento', 'WordPress', 'JavaScript', 'Angular JS', 'C#', 'Flask', 'SDK']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                            text='Recommended skills generated from System', value=recommended_skills, key='3')
                        rec_course = course_recommender(web_course)
                        break

                    #### Android App Development
                    elif skill_cleaned in android_keyword:
                        print(f"✅ Matched: {skill} (Android Development)")
                        reco_field = 'Android Development'
                        st.success("** Our analysis says you are looking for Android App Development Jobs **")
                        recommended_skills = ['Android', 'Android development', 'Flutter', 'Kotlin', 'XML', 'Java', 'Kivy', 'GIT', 'SDK', 'SQLite']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                            text='Recommended skills generated from System', value=recommended_skills, key='4')
                        rec_course = course_recommender(android_course)
                        break

                    #### IOS App Development
                    elif skill_cleaned in ios_keyword:
                        print(f"✅ Matched: {skill} (iOS Development)")
                        reco_field = 'IOS Development'
                        st.success("** Our analysis says you are looking for IOS App Development Jobs **")
                        recommended_skills = ['IOS', 'IOS Development', 'Swift', 'Cocoa', 'Cocoa Touch', 'Xcode', 'Objective-C', 'SQLite', 'Plist', 'StoreKit', "UI-Kit", 'AV Foundation', 'Auto-Layout']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                            text='Recommended skills generated from System', value=recommended_skills, key='5')
                        rec_course = course_recommender(ios_course)
                        break

                    #### UI-UX Recommendation
                    elif skill_cleaned in uiux_keyword:
                        print(f"✅ Matched: {skill} (UI-UX Development)")
                        reco_field = 'UI-UX Development'
                        st.success("** Our analysis says you are looking for UI-UX Development Jobs **")
                        recommended_skills = ['UI', 'User Experience', 'Adobe XD', 'Figma', 'Zeplin', 'Balsamiq', 'Prototyping', 'Wireframes', 'Storyframes', 'Adobe Photoshop', 'Editing', 'Illustrator', 'After Effects', 'Premier Pro', 'Indesign', 'Wireframe', 'Solid', 'Grasp', 'User Research']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                            text='Recommended skills generated from System', value=recommended_skills, key='6')
                        rec_course = course_recommender(uiux_course)
                        break

                    #### For Not Any Recommendations
                    elif skill_cleaned in n_any:
                        print(f"✅ Matched: {skill} (General Skills - No Specific Category)")
                        reco_field = 'General'
                        st.warning("** Currently, our tool only predicts and recommends for Data Science, Web, Android, IOS, and UI/UX Development**")
                        recommended_skills = ['No Recommendations']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                            text='Currently No Recommendations', value=recommended_skills, key='6')
                        rec_course = "Sorry! Not Available for this Field"
                        break

                    else:
                        print(f"❌ No match found for: {skill}")

                # Process resume text with spaCy
                doc = nlp(resume_text)
                # Extract skills using the processed document
                skills_data = extract_skills(doc, list(doc.noun_chunks))

                # Display current skills by category
                st.subheader("**Your Current Skills 🎯**")
                for category, skills in skills_data['categorized'].items():
                    if skills:  # Only show categories that have skills
                        st.write(f"**{category.replace('_', ' ').title()}:**")
                        st.write(", ".join(skills))

                # Generate recommendations based on missing skills in each category
                st.subheader("**Recommended Skills 💡**")
                for category, skills in skills_data['categorized'].items():
                    if category in SKILLS_DB['technical']:
                        missing_skills = set(SKILLS_DB['technical'][category]) - set(skills)
                        if missing_skills:
                            st.write(f"**{category.replace('_', ' ').title()}:**")
                            st.write(", ".join(list(missing_skills)[:5]))  # Show top 5 recommendations

                ## Resume Scorer & Resume Writing Tips
                st.subheader("**Resume Tips & Ideas 🥂**")
                resume_score = 0
                
                ### Predicting Whether these key points are added to the resume
                SCORING_CRITERIA = {
                    "Objective/Summary": (["objective", "summary"], 6),
                    "Education": (["education", "school", "college"], 12),
                    "Experience": (["experience"], 16),
                    "Internships": (["internship", "internships"], 6),
                    "Skills": (["skills", "skill"], 7),
                    "Hobbies": (["hobbies", "hobby"], 4),
                    "Interests": (["interests", "interest"], 5),
                    "Achievements": (["achievements", "achievement"], 13),
                    "Certifications": (["certifications", "certification"], 12),
                    "Projects": (["projects", "project"], 19)
                }

                def calculate_resume_score(resume_text):
                    resume_text = resume_text.lower()  # Convert to lowercase for case-insensitive search
                    resume_score = 0

                    for section, (keywords, score) in SCORING_CRITERIA.items():
                        if any(keyword in resume_text for keyword in keywords):
                            resume_score += score
                            st.markdown(f'''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added {section}</h5>''', unsafe_allow_html=True)
                        else:
                            st.markdown(f'''<h5 style='text-align: left; color: #000000;'>[-] Please add {section}.</h5>''', unsafe_allow_html=True)

                    return resume_score

                # Example usage where resume_text is extracted earlier in your code
                resume_score = calculate_resume_score(resume_text)

                st.subheader("**Resume Score 📝**")
                
                st.markdown(
                    """
                    <style>
                        .stProgress > div > div > div > div {
                            background-color: #d73b5c;
                        }
                    </style>""",
                    unsafe_allow_html=True,
                )

                ### Score Bar
                my_bar = st.progress(0)
                score = 0
                for percent_complete in range(resume_score):
                    score +=1
                    time.sleep(0.1)
                    my_bar.progress(percent_complete + 1)

                ### Score
                st.success('** Your Resume Writing Score: ' + str(resume_score)+'**')
                st.warning("** Note: This score is calculated based on the content that you have in your Resume. **")



                ### Getting Current Date and Time
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date+'_'+cur_time)


                ## Calling insert_data to add all the data into user_data                
                insert_data(str(sec_token), str(ip_add), (host_name), (dev_user), (os_name_ver), (act_name), (act_mail), (act_mob), resume_data['name'], resume_data['email'], str(resume_score), timestamp, str(resume_data['no_of_pages']), reco_field, cand_level, str(resume_data['skills']), str(recommended_skills), str(rec_course), pdf_name)

                ## Recommending Resume Writing Video
                st.header("**Bonus Video for Resume Writing Tips💡**")
                resume_vid = random.choice(resume_videos)
                st.video(resume_vid)

                ## Recommending Interview Preparation Video
                st.header("**Bonus Video for Interview Tips💡**")
                interview_vid = random.choice(interview_videos)
                st.video(interview_vid)

                ## On Successful Result 
                st.balloons()

            else:
                st.error('Something went wrong..')                


    ###### CODE FOR FEEDBACK SIDE ######
    elif choice == 'Feedback':   
        
        # timestamp 
        ts = time.time()
        cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        timestamp = str(cur_date+'_'+cur_time)

        # Feedback Form
        with st.form("my_form"):
            st.write("Feedback form")            
            feed_name = st.text_input('Name')
            feed_email = st.text_input('Email')
            feed_score = st.slider('Rate Us From 1 - 5', 1, 5)
            comments = st.text_input('Comments')
            Timestamp = timestamp        
            submitted = st.form_submit_button("Submit")
            if submitted:
                ## Calling insertf_data to add dat into user feedback
                insertf_data(feed_name,feed_email,feed_score,comments,Timestamp)    
                ## Success Message 
                st.success("Thanks! Your Feedback was recorded.") 
                ## On Successful Submit
                st.balloons()    


        # query to fetch data from user feedback table
        query = 'select * from user_feedback'        
        plotfeed_data = pd.read_sql(query, connection)                        


        # fetching feed_score from the query and getting the unique values and total value count 
        labels = plotfeed_data.feed_score.unique()
        values = plotfeed_data.feed_score.value_counts()


        # plotting pie chart for user ratings
        st.subheader("**Past User Rating's**")
        fig = px.pie(values=values, names=labels, title="Chart of User Rating Score From 1 - 5", color_discrete_sequence=px.colors.sequential.Aggrnyl)
        st.plotly_chart(fig)


        #  Fetching Comment History
        cursor.execute('select feed_name, comments from user_feedback')
        plfeed_cmt_data = cursor.fetchall()

        st.subheader("**User Comment's**")
        dff = pd.DataFrame(plfeed_cmt_data, columns=['User', 'Comment'])
        st.dataframe(dff, width=1000)

    
    ###### CODE FOR ABOUT PAGE ######
    elif choice == 'About':   

        st.subheader("**About The Tool - AI RESUME ANALYZER**")

        st.markdown('''

        <p align='justify'>
            A tool which parses information from a resume using natural language processing and finds the keywords, cluster them onto sectors based on their keywords. And lastly show recommendations, predictions, analytics to the applicant based on keyword matching.
        </p>

        <p align="justify">
            <b>How to use it: -</b> <br/><br/>
            <b>User -</b> <br/>
            In the Side Bar choose yourself as user and fill the required fields and upload your resume in pdf format.<br/>
            Just sit back and relax our tool will do the magic on it's own.<br/><br/>
            <b>Feedback -</b> <br/>
            A place where user can suggest some feedback about the tool.<br/><br/>
            <b>Admin -</b> <br/>
            <!--For login use <b>admin</b> as username and <b>admin1</b> as password.<br/> -->
            It will load all the required stuffs and perform analysis.
        </p><br/><br/>


        ''',unsafe_allow_html=True)  


    ###### CODE FOR ADMIN SIDE (ADMIN) ######
    else:
        st.success('Welcome to Admin Side')

        # Admin Login
        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')

        if st.button('Login'):

            ## Credentials 
            if ad_user == 'admin' and ad_password == 'admin1':

                ### Fetch miscellaneous data from user_data(table) and convert it into dataframe
                cursor.execute('''SELECT ID, ip_add, resume_score, convert(Predicted_Field using utf8), User_Level FROM user_data''')
                datanalys = cursor.fetchall()

                plot_data = pd.DataFrame(datanalys, columns=['Idt','IP_add', 'resume_score', 'Predicted_Field', 'User_Level'])
                
                # Decode 'Predicted_Field' and 'User_Level' columns if they are in bytes
                plot_data['Predicted_Field'] = plot_data['Predicted_Field'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)
                plot_data['User_Level'] = plot_data['User_Level'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)

                ### Total Users Count with a Welcome Message
                values = plot_data.Idt.count()
                st.success("Welcome Admin ! Total %d " % values + " User's Have Used Our Tool : )")                

                ### Fetch user data from user_data(table) and convert it into dataframe
                cursor.execute('''SELECT ID, sec_token, ip_add, act_name, act_mail, act_mob, convert(Predicted_Field using utf8), Timestamp, Name, Email_ID, resume_score, Page_no, pdf_name, convert(User_level using utf8), convert(Actual_skills using utf8), convert(Recommended_skills using utf8), convert(Recommended_courses using utf8), os_name_ver, host_name, dev_user from user_data''')
                data = cursor.fetchall()                 

                st.header("**User's Data**")
                df = pd.DataFrame(data, columns=['ID', 'Token', 'IP Address', 'Name', 'Mail', 'Mobile Number', 'Predicted Field', 'Timestamp',
                                                'Predicted Name', 'Predicted Mail', 'Resume Score', 'Total Page',  'File Name',   
                                                'User Level', 'Actual Skills', 'Recommended Skills', 'Recommended Course',
                                                'Server OS', 'Server Name', 'Server User',])

                ### Viewing the dataframe
                st.dataframe(df)

                ### Downloading Report of user_data in csv file
                st.markdown(get_csv_download_link(df,'User_Data.csv','Download Report'), unsafe_allow_html=True)

                ### Fetch feedback data from user_feedback(table) and convert it into dataframe
                cursor.execute('''SELECT * from user_feedback''')
                data = cursor.fetchall()

                st.header("**User's Feedback Data**")
                df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Feedback Score', 'Comments', 'Timestamp'])
                st.dataframe(df)

                ### query to fetch data from user_feedback(table)
                query = 'select * from user_feedback'
                plotfeed_data = pd.read_sql(query, connection)                        

                ### Analyzing All the Data's in pie charts

 
                # fetching Predicted_Field from the query and getting the unique values and total value count                 
                labels = plot_data.Predicted_Field.unique()
                values = plot_data.Predicted_Field.value_counts()

                # Pie chart for predicted field recommendations
                st.subheader("**Pie-Chart for Predicted Field Recommendation**")
                fig = px.pie(df, values=values, names=labels, title='Predicted Field according to the Skills 👽', color_discrete_sequence=px.colors.sequential.Aggrnyl_r)
                st.plotly_chart(fig)

                # fetching User_Level from the query and getting the unique values and total value count                 
                labels = plot_data.User_Level.unique()
                values = plot_data.User_Level.value_counts()

                # Pie chart for User's👨‍💻 Experienced Level
                st.subheader("**Pie-Chart for User's Experienced Level**")
                fig = px.pie(df, values=values, names=labels, title="Pie-Chart 📈 for User's 👨‍💻 Experienced Level", color_discrete_sequence=px.colors.sequential.RdBu)
                st.plotly_chart(fig)

                # fetching resume_score from the query and getting the unique values and total value count                 
                labels = plot_data.resume_score.unique()                
                values = plot_data.resume_score.value_counts()

                # Pie chart for Resume Score
                st.subheader("**Pie-Chart for Resume Score**")
                fig = px.pie(df, values=values, names=labels, title='From 1 to 100 💯', color_discrete_sequence=px.colors.sequential.Agsunset)
                st.plotly_chart(fig)




            ## For Wrong Credentials
            else:
                st.error("Wrong ID & Password Provided")

# Calling the main (run()) function to make the whole process run
run()