import pandas as pd
import streamlit as st 
from streamlit_option_menu import option_menu
from PIL import Image
import easyocr
import re
import cv2
import numpy as np
import io
import psycopg2
import pymysql


st.set_page_config(page_title="BizcardX: Extraction Business Card Data with OCR",
                   layout="wide",
                   initial_sidebar_state="expanded")

st.header(":violet[BizcardX: Extraction Business Card Data with OCR]")

Selected=option_menu(None,["Home","Upload & Extract","Modify"],
                     icons=["house","cloud-upload","pencil-square"],
                     orientation="horizontal")

#Connection Mysql
myconnection=pymysql.connect(host="127.0.0.1",
                             user="root",
                             password="kishore22",
                             database="Project")

cur=myconnection.cursor()
#cur.execute("drop table Card_data")
cur.execute('''create table if not exists Card_data(id int AUTO_INCREMENT Primary key,
                                        company_name Text,
                                        card_holder Text,
                                        designation Text,
                                        mobile_number varchar(50),
                                        Email_id Text,
                                        website Text,
                                        area Text,
                                        city Text,
                                        state Text,
                                        pincode varchar(10),
                                        image LONGBLOB)''')



if Selected=="Home":
    st.markdown("## :blue[**Technologies Used :**] Python,easy OCR, Streamlit, SQL, Pandas")
    st.markdown("## :blue[**Overview :**] In this streamlit web app you can upload an image of a business card and extract relevant information from it using easyOCR. You can view, modify or delete the extracted data in this app. This app would also allow users to save the extracted information into a database along with the uploaded business card image. The database would be able to store multiple entries, each with its own business card image and extracted information.")

 
if Selected=="Upload & Extract":
    st.markdown("### :green[Update a Business Card]")
    Uploaded_card=st.file_uploader("Upload_here",label_visibility="collapsed",type=["png","jpeg","jpg"])

    if Uploaded_card is not None:
        st.image(Uploaded_card,caption="Uploaded_card",use_column_width=True)

        #image_binary=Uploaded_card.read()

        read=easyocr.Reader(["en"])
        reader_easyocr = read
        Card_image=Image.open(Uploaded_card)
        add_1=read.readtext(np.array(Card_image),detail=0)


        st.markdown("### :green[CARD Information]")


        data={"Name":[],"Designation":[],"Company":[],"Contact":[],
        "Email":[],"Website":[],
        "Area":[],"City":[],"State":[],"Pincode":[]
        }

        def Upload_image(Card_data):

            for ind,i in enumerate(add_1):
                #Name 
                if ind==0:
                    data["Name"].append(i)
                #Designation
                elif ind==1:
                    data["Designation"].append(i)
                #Contact
                elif i.startswith("+") or (i.replace("-","").isdigit()) or "-" in i:
                    data["Contact"].append(i)
                #Email_id
                elif "@" in i and ".com" in i:
                    smaller=i.lower()
                    data["Email"].append(smaller)
                #website
                elif "www" in i or "wwW" in i or "WWW" in i:
                    smaller=i.lower()
                    data["Website"].append(smaller) 

                # To get COMPANY NAME  
                elif ind == len(add_1)-1:
                    data["Company"].append(i)

                #Area
                if re.findall('^[0-9].+,[a-zA-Z]+',i):
                    data["Area"].append(i.split(',')[0])
                elif re.findall('[0-9] [a-zA-Z]+',i):
                    data["Area"].append(i) 
                

                #CITY NAME
                match1 = re.findall('.+St , ([a-zA-Z]+).+', i)
                match2 = re.findall('.+St,, ([a-zA-Z]+).+', i)
                match3 = re.findall('^[E].*',i)
                if match1:
                    data["City"].append(match1[0])
                elif match2:
                    data["City"].append(match2[0])
                elif match3:
                    data["City"].append(match3[0])

                #STATE
                state_match = re.findall('[a-zA-Z]{9} +[0-9]',i)
                if state_match:
                        data["State"].append(i[:9])
                elif re.findall('^[0-9].+, ([a-zA-Z]+);',i):
                    data["State"].append(i.split()[-1])
                if len(data["State"])== 2:
                    data["State"].pop(0)

                #PINCODE        
                if len(i)>=6 and i.isdigit():
                    data["Pincode"].append(i)
                elif re.findall('[a-zA-Z]{9} +[0-9]',i):
                    data["Pincode"].append(i[10:])
        Upload_image(add_1)

        #data_information 
        data_1=pd.DataFrame(data)

        #image_to_bytes
        im_by=io.BytesIO()
        Card_image.save(im_by,format="png")
        im_data=im_by.getvalue()

        dic1={"Image":[im_data]}
        img_bin=pd.DataFrame(dic1)
        Image_df=pd.concat([data_1,img_bin],axis=1)
        st.dataframe(Image_df)

        #Upload data to database
        if st.button("Upload to Database"):
            for index,row in Image_df.iterrows():
                sql='''insert into card_data(card_holder,
                                                designation,
                                                company_name,
                                                mobile_number,
                                                email_id,
                                                website,
                                                area,
                                                city,
                                                state,
                                                pincode,
                                                image)
                            values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
                


                values=(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10])
                cur.execute(sql,values)
                myconnection.commit()
                st.success("### uploaded to database successfully")

#Modify-Menu
if Selected=="Modify":
    col1,col2,col3=st.columns([3,3,2])
    col2.markdown("### Alter or Delete the data here")
    columns1,columns2=st.columns(2,gap="large")
    try:
        with columns1:
            cur.execute("select card_holder from card_data")
            result=cur.fetchall()
            business_cards={}
            for row in result:
                business_cards[row[0]]= row[0]
            selected_card=st.selectbox("Select a card holder name to update",list(business_cards.keys()))
            st.markdown("### Update or modify any data below")
            cur.execute("select company_name,card_holder,designation,mobile_number,Email_id,website,area,city,state,pincode from card_data WHERE card_holder=%s",(selected_card,))
            result=cur.fetchone()

            #Displaying all The Informations
            company_name=st.text_input("company_name",result[0])
            card_holder=st.text_input("Card_holder",result[1])
            designation=st.text_input("designation",result[2])
            mobile_number=st.text_input("Mobile_number",result[3])
            email_id=st.text_input("Email_id",result[4])
            website=st.text_input("Website",result[5])
            area=st.text_input("Area",result[6])
            city=st.text_input("City",result[7])
            state=st.text_input("State",result[8])
            pincode=st.text_input("Pincode",result[9])

            if st.button("Commit changes to DB"):
                #Update the information
                cur.execute("""UPDATE card_data SET company_name=%s,card_holder=%s,designation=%s,mobile_number=%s,email_id=%s,website=%s,area=%s,city=%s,state=%s,pincode=%s
                            WHERE card_holder=%s""",(company_name,card_holder,designation,mobile_number,email_id,website,area,city,state,pincode,selected_card))
                myconnection.commit()
                st.success("Information updated in database successfully")

        with columns2:
            cur.execute("select card_holder from card_data")
            result=cur.fetchall()
            business_cards={}
            for row in result:
                business_cards[row[0]]= row[0]
            selected_card=st.selectbox("select a card_holder name to delete",list(business_cards.keys()))
            st.write(f"### you have selected :green[**{selected_card}'s**] card to delete")
            st.write("#### Proceed to delete this card")

            if st.button("Yes, Delete Busniess Card"):
                cur.execute(f"DELETE from card_holder WHERE card_holder='{selected_card}")
                myconnection.commit()
                st.success("Business card information deleted from database")
    except:
        st.warning("there is no data available in the database")

    if st.button("View updated data"):
        upload_df=pd.read_sql_query("select company_name,card_holder,designation,mobile_number,Email_id,website,area,city,state,pincode from card_data",myconnection)
        st.write(upload_df)