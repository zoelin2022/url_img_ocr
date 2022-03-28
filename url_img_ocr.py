from selenium import webdriver
from selenium.webdriver.common.by import By 
import cv2
import pytesseract # 裁切
from PIL import Image # 顯示圖檔
import pymysql
import base64 # 圖片轉base64編碼
import time

def db_init():
    db = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='root',
        port=8889,
        db='test'
    )
    cursor = db.cursor(pymysql.cursors.DictCursor)
    return db, cursor

# 瀏覽器設定
chrome_options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=chrome_options)
    
def web_screenshot(url):
    driver.get(url)
    # 滑動到指定位置
    jsCode = "var q=document.documentElement.scrollTop=800"
    driver.execute_script(jsCode)
    time.sleep(3)
    # 截圖
    driver.get_screenshot_as_file("screen.png")
    
def crop_pic():
    # open_img = Image.open("screen.png")
    # open_img.show()
    # 讀取圖檔
    read_img = cv2.imread("screen.png")
    x, y = 610, 585 # 裁切區域的座標(左上角)
    w, h = 1106, 260 # 裁切區域的長寬
    # 裁切圖片
    crop_img = read_img[y:y+h, x:x+w]
    # 寫入圖檔
    cv2.imwrite("crop.png", crop_img)

def img_to_text():
    # 打開擷取好辨識範圍的圖檔
    img = Image.open("crop.png")
    # img.show()
    # time.sleep(3)
    # 辨識文字
    content = pytesseract.image_to_string(img, lang="chi_tra")
    content = content.replace(' ', '').split("\n")
    text = content[0] # 只取第一行
    return text

def img_to_code():
    # 讀取檔案
    with open ("crop.png", mode="rb") as file:
        img = file.read()
    # base64編碼
    base64_data = base64.b64encode(img)  
    img_code = str(base64_data, 'utf-8') #去掉字串前面的 b
    return img_code

def img_save_to_db():
    db, cursor = db_init()
    text = img_to_text()
    img_code = img_to_code()
    # 存入db
    sql=f"INSERT INTO `ocr_img`.`pic` (content,code) VALUES  ('{text}','{img_code}')"
    cursor.execute(sql)
    db.commit()
    db.close()
    
def db_select_data():  
    db, cursor = db_init()
    # 取出最新一筆的文字跟圖片編碼
    sql = f"SELECT `content`,`code` FROM ocr_img.pic ORDER BY id DESC LIMIT 0 , 1;"
    cursor.execute(sql)
    values = cursor.fetchall()
    ans_text = values[0]['content']
    code = (values[0]['code'])
    db.commit()
    db.close()
    # 將db的base64還原成圖片
    values_str = str(code)
    with open('dba_submit.png', 'wb') as file:
        new_pic = base64.b64decode(values_str)  # 解碼
        file.write(new_pic)  # 將解碼得到的資料寫入到圖片中
    # 打開還原好的圖檔
    # img = Image.open("dba_submit.png")
    # img.show()
    return ans_text
    
def upload(url):
    driver.get(url)
    ans_text = db_select_data()
    # 增加一個input，填入辨識文字
    jscode = f'document.getElementsByClassName("me-2")[1].after($anwser);$anwser.value = "{ans_text}";'
    driver.execute_script(jscode)
    # 定位上傳檔案按鈕
    upfile = driver.find_element(By.ID,"img_src")
    # 使用send_keys方法上傳檔案(使用絕對路徑)
    upfile.send_keys(r"/Users/lin/Desktop/python/dba_submit.png")
    # 點擊送出button
    # driver.find_element_by_xpath('//*[@id="handover"]/div/div/div/form/div[4]/div/button').click()

try:
    # 1. 至網站截取畫面
    web_screenshot("https://ntc.im/pn/")
    # 2. 裁切圖及解析第一行文字,存入MySQL
    crop_pic()
    img_save_to_db()
    # 3. 在網站裡增加一個欄位,填入自己的名字
    # 4. 從存入MySQL的table查詢出文字和圖檔後上傳
    upload("https://ntc.microtrend.tw/202202?classid=DV101&studentid=19")
except Exception as e:
    print("except"+ str(e))
