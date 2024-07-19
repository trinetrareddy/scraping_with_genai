import streamlit as st
from bs4 import BeautifulSoup, Comment
import subprocess
import os
import traceback

import openai
openai.api_key = ""


def get_string_from_file(file_path):
    """
    Reads HTML content from a file and returns it as a string

    Args:
      file_path (str): Path to the file

    Returns:
      str: HTML content as a string
    """
    f = open(file_path, 'r')
    html_string = f.read()
    f.close()
    return html_string



def strip_html_elem_of(html_elem, strip_of):
    """
    Removes specified HTML elements from a BeautifulSoup HTML object

    Args:
      html_elem (BeautifulSoup): BeautifulSoup HTML object
      strip_of (list): List of HTML elements to remove
    """
    list_tags = []
    list_tags_to_remove = []
    list_tag_names = []
    for tag in html_elem.descendants:
        if tag is not None:
            if tag.name is not None and tag.name in strip_of:
                list_tags_to_remove.append(tag)
            else:
                list_tags.append(tag)
                list_tag_names.append(tag.name)
    for rem_tag in list_tags_to_remove:
        rem_tag.extract()

def grab_html_wo_script(response, dump_path):
    """
    Gets HTML content without script tags from a server response

    Args:
      response (str): Server response containing the HTML content
      dump_path (str): Path to dump the stripped HTML content

    Returns:
      str: Stripped HTML content
    """
    html_object = BeautifulSoup(response,'html.parser')
    print("Removing all comments from html response")
    for comment in html_object.find_all(text=lambda text: isinstance(text, Comment)):
        comment.extract()
    body=html_object.find('body')
    strip_of_elems_body = ['iframe','script','noscript','table','style']
    strip_html_elem_of(body,strip_of_elems_body)
    head=html_object.find('head')
    strip_of_elems_head = ['iframe','script','noscript','style']
    strip_html_elem_of(head,strip_of_elems_head)
    stripped_html = html_object.prettify()
    print(stripped_html, file=open(dump_path,'w'))
    return stripped_html

def get_no_of_lines_tag(tag):
    """
    Calculates the number of lines occupied by an HTML tag in a string representation of the tag

    Args:
      tag (BeautifulSoup): BeautifulSoup HTML tag

    Returns:
      int: Number of lines occupied by the tag
    """
    string_tag = str(tag)
    no_of_lines = len(string_tag.splitlines())
    return no_of_lines

def get_no_of_chars_in_tag(tag):
    """
    Get the number of characters in a tag.

    Args:
        tag (Tag): The tag object.

    Returns:
        int: The number of characters in the tag.
    """
    string_tag = str(tag)
    length_tag = len(string_tag)
    return length_tag


def find_children_to_split(tag,tag_length):
    """
    Find the children of a tag that need to be split.

    Args:
        tag (Tag): The tag object.
        tag_length (int): The number of characters in the tag.

    Returns:
        list: The list of children tags to be split.
        list: The list of lengths of the children tags.
    """
    #print(type(tag))
    children = tag.find_all(recursive=False)
    if len(children) == 1:
      tag = children[0]
      tag_length = get_no_of_chars_in_tag(tag)
      children, child_lines = find_children_to_split(tag,tag_length)
    else:
      child_lines = []
      for child in children:
        child_length = get_no_of_chars_in_tag(child)
        child_lines.append(child_length)
    return children, child_lines



def get_indices_for_split(list_lengths):
    """
    Get the indices at which to split a list of lengths.

    Args:
        list_lengths (list): The list of lengths.

    Returns:
        list: The final indices to split the list.
    """
    print("List lengths of children to prune: ",list_lengths)
    # Perform argsort
    argsort_result = sorted(enumerate(list_lengths), key=lambda x: x[1])

    # Extract the sorted indices
    sorted_indices = [index for index, value in argsort_result]
    print("sorted_indices: ",sorted_indices)
    sorted_list_lengths = sorted(list_lengths)
    sum_lengths = sum(list_lengths)
    print("SUM of lengths of children: ",sum_lengths)
    temp_sum = 0
    break_point = -1
    for i in range(len(sorted_list_lengths)):
      temp_sum += sorted_list_lengths[i]
      if temp_sum > character_limit_html:
        break_point = i - 1
        break
    if break_point == -1:
      break_point = 0
    print("BreakPoint: ", break_point)
    final_indices = sorted_indices[:break_point+1]
    print("Final Indices: ", final_indices)
    # for i in range(len(list_lengths)):
    #   if sorted_indices[i] < break_point:
    #     final_indices.append(i)
    return final_indices


def split_html_into_parts(html_string,list_html_strings=list()):
    """
    Split an HTML string into parts.

    Args:
        html_string (str): The HTML string to split.
        list_html_strings (list): The list of HTML strings.

    Returns:
        list: The list of HTML strings after splitting.
    """
    print("#########SPLIT_HTML_INTO_PARTS CALLED###########")
    #print(html_string)
    html_object = BeautifulSoup(html_string,'html.parser')
    #print(type(html_object))
    html_object_2 = BeautifulSoup(html_object.prettify(),'html.parser')
    body = html_object.find('body')
    body2 = html_object_2.find('body')
    
    body_length = get_no_of_chars_in_tag(body)
    print("PRE Length of HTML: ,",body_length)
    body2_length = get_no_of_chars_in_tag(body2)
    assert body_length == body2_length
    
    desc_of_body, desc_lines = find_children_to_split(body, body_length)
    desc_of_body_2, desc_lines_2 = find_children_to_split(body2, body2_length )
    assert desc_lines == desc_lines_2
    
    first_indices = get_indices_for_split(desc_lines)
    #print("First Indices: ", first_indices)
    print("lenghts of desc of body, desc of body2, desc_lines, desc_lines_2: ", len(desc_of_body),len(desc_of_body_2), len(desc_lines), len(desc_lines_2))
    for i in range(len(desc_lines)):
      
      if i in first_indices:
        #print("I: ",i)
        #print("Extracting tags from html_2", desc_lines_2[i])
        desc_of_body_2[i].extract()
      else:
        #print("Extracting tags from html_1", desc_lines[i])
        #pre_extracting_body_size = get_no_of_chars_in_tag(body)
        desc_of_body[i].extract()
        #post_extracting_body_size = get_no_of_chars_in_tag(body)
        #print("Body size reduced from: ", pre_extracting_body_size," to: ", post_extracting_body_size)
    body_length_post = get_no_of_chars_in_tag(body)
    html_string_1 = html_object.prettify()
    print("POST Length of 1st HTML: ",body_length_post)

    body2_length_post = get_no_of_chars_in_tag(body2)
    html_string_2 = html_object_2.prettify()
    print("POST Length of 2nd HTML: ",body2_length_post)

    if len(desc_lines) == 0:
      len_html_strings = len(list_html_strings)
      print(body,body2)
      st.write("##ERROR##", f"two of the html split files are too big. Check once - {len_html_strings}th and {len_html_strings+1}th splits" )
      list_html_strings.append(html_string_1)
      list_html_strings.append(html_string_2)
      return list_html_strings
    

    if body_length_post > character_limit_html:
      
      print("Sending 1st HTML to split again. Length: ", body_length_post, len(html_string_1))
      split_html_into_parts(html_string_1,list_html_strings)
    else:
      print("Adding 1st html to list_html_strings", len(list_html_strings))
      list_html_strings.append(html_string_1)
    
    if body2_length_post > character_limit_html:
      
      print("Sending 2nd HTML to split again. Length: ", body2_length_post, len(html_string_2))
      split_html_into_parts(html_string_2,list_html_strings)
    else:
      print("Adding 2nd html to list_html_strings", len(list_html_strings))
      list_html_strings.append(html_string_2)

    return list_html_strings

@st.cache_data
def does_html_strip_contain(user_requirements,html):
    """
    Checks if the given HTML strip contains the values the user wishes to extract.
    
    Args:
        user_requirements (str): The user requirements to be checked.
        html (str): The HTML strip to analyze.
        
    Returns:
        str: "Yes" or "No" indicating whether the HTML contains the desired values.
    """
    response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo-16k",
      messages=[
        {
            "role": "system",
            "content": """
You are an expert website analyzer for a web scraping process.
Take the user requirements and say if the html given contains the values user wishes to extract.
Don't explain anything, just say "Yes/No".
            """
        },
        {
          "role": "user",
          "content": f"""
You are an expert website analyzer for a web scraping process.
Take the user requirements and say if the html given contains the values user wishes to extract.
Don't explain anything, just say "Yes/No".

USER REQUIREMENTS:
{user_requirements}

HTML CODE YOU NEED TO ANALYZE:
{html}
          """,
        }
      ],
      temperature=1,
      max_tokens=1,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0
    )
    return response['choices'][0]['message']['content']

@st.cache_data
def clean_code_indentation(code):
    """
    Cleans the indentation of a Python scraping code.
    
    Args:
        code (str): The Python scraping code to be cleaned.
        
    Returns:
        str: The cleaned and bug-free Python script.
    """
    response = openai.ChatCompletion.create(
      model="gpt-4",
      messages=[
        {
            "role": "system",
            "content": """
You are an expert software developer. 
A python scraping code will be given to you. 
Do not alter any of the logic. If there are any indentation or syntax errors, correct them.
And return a bug free runnable python script.
Don't explain the code, just generate the code block itself.
            """
        },
        {
          "role": "user",
          "content": f"""
You are an expert software developer. 
A python scraping code will be given to you. 
Do not alter any of the logic. If there are any indentation or syntax errors, correct them.
And return a bug free runnable python script.
Don't explain the code, just generate the code block itself.

CODE:
{code}""",
        }
      ],
      temperature=1,
      max_tokens=1000,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0
    )
    return response['choices'][0]['message']['content']


@st.cache_data
def get_chat_response(requirements, html):
  response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
      {
          "role": "system",
          "content": """
You are an expert website analyzer for a web scraping process.
Take the user requirements and convert it into clean python code to scrape the website.
Make sure there are no indentation issues
Don't explain the code, just generate the code block itself.
          """
      },
      {
        "role": "user",
        "content": f"""
You are an expert website analyzer for a web scraping process.
Take the user requirements and convert it into clean python code to scrape the website. 
Make sure there are no indentation issues
Don't explain the code, just generate the code block itself.

USER REQUIREMENTS:
{requirements}

HTML CODE YOU NEED TO SCRAPE:
{html}

FINISH THE PYTHON CODE TO SCRAPE THE WEBSITE:

from bs4 import BeautifulSoup
import json

# Get the URL of the website
with open('./results/denver.html') as f:
    response = f.read()

html_soup = BeautifulSoup(response, 'html.parser')
""",
      }
    ],
    temperature=1,
    max_tokens=500,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
  )
  return response['choices'][0]['message']['content']


st.title("Scraping Code Generator")

# Use st.file_uploader() to allow the user to upload a file
uploaded_file = st.file_uploader("Upload a file", type=["html"])



# Check if a file has been uploaded
if uploaded_file is not None:
    st.success("File successfully uploaded.")
    character_limit_html = st.number_input("Max Characters in one split", min_value=10000, max_value=25000, value=15000) # @param {type:"integer"}
    html_string = uploaded_file.read()
    # st.markdown(f'<iframe>{html_string}</iframe>', unsafe_allow_html=True)
    file_name = uploaded_file.name
    file_name_wo_ext = "".join(file_name.split(".")[:-1])
    root_path = f"./output_files/{file_name_wo_ext}/"
    error_path = f"./error_files/{file_name_wo_ext}/"
    try:
        os.mkdir(root_path)
        print(f"Directory '{root_path}' created successfully.")
    except FileExistsError:
        print(f"Directory '{root_path}' already exists.")
    except OSError as e:
        print(f"An error occurred: {e}")

    try:
        os.mkdir(error_path)
        print(f"Directory '{error_path}' created successfully.")
    except FileExistsError:
        print(f"Directory '{error_path}' already exists.")
    except OSError as e:
        print(f"An error occurred: {e}")

    stripped_html_path = f'{root_path}stripped_{file_name}'
    full_stripped_html_path = stripped_html_path

    SCRAPING_CODE = f"""
from bs4 import BeautifulSoup
import json
f = open(\"{stripped_html_path}\", 'r')
html_string = f.read()
f.close()
html_soup = BeautifulSoup(html_string, 'html.parser')
"""

    stripped_html = grab_html_wo_script(html_string,dump_path=full_stripped_html_path)

    placeholder_requirements = "Extract all the reviews from the html. For each review, get the review title, review message, reviewer name, ratings given by reviewer. Also if there is an overall rating for the product in the html page, get that also separately."
    user_requirements = st.text_area("Enter what all to scrape",placeholder_requirements)

    requirements = f"{user_requirements} Make sure the code prints these values from the html page in json format."

    stripped_htmls = split_html_into_parts(stripped_html, list_html_strings=list())
    print(len(stripped_htmls))
    useful_stripped_htmls = []
    for i in range(len(stripped_htmls)):
        html_stripped = stripped_htmls[i]
        try:
          gpt_response = does_html_strip_contain(user_requirements,html_stripped)
        except Exception as e:
           st.write("ERROR FROM GPT Server while detecting split html: ", e)
           error_file_path = f"{error_path}stripped_{file_name}".replace(".html",f"_{i}.html")
           print(html_stripped,file=open(error_file_path,'w'))
           break
        print("GPT response: ",gpt_response)
        if gpt_response == "Yes":
            file_path  = str(full_stripped_html_path).replace(".html",f"_{i}.html")
            print(file_path)
            useful_stripped_htmls.append(html_stripped)
            print(html_stripped, file=open(file_path,'w'))

    for i in range(len(useful_stripped_htmls)):
        print(i)
        html_stripped = useful_stripped_htmls[i]
        try:
          code = get_chat_response(requirements, html_stripped)
        except Exception as e:
           st.write("ERROR FROM GPT Server while extracting code: ", e)
           break
        print("CODE: ","\n\n\n")
        print(code.strip(),'\n*****************')

        final_code = f"""\n{SCRAPING_CODE}\n{code.strip()}"""
        # cleaned_final_code = clean_code_indentation(final_code)
        # cleaned_final_code = cleaned_final_code.replace('```python',"")
        # cleaned_final_code = cleaned_final_code.replace('```',"")
        print(final_code,file=open(f'{root_path}python_code_{i}.py','w'))
        result = subprocess.run(['python',f'{root_path}python_code_{i}.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        st.write(f"############\nOutput for {i}th code: ", result.stdout)
        error = result.stderr
        error = error.strip()
        if len(error) > 0:
          st.write(f"************\nError for {i}th code: ", result.stderr)
          print("***************ERROR**************\n",error)