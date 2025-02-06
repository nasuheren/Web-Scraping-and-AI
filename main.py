from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from dotenv import load_dotenv
import os
import openai
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager


def send_to_ai(content):
    # .env dosyasını yükle
    load_dotenv()

    # Ortam değişkeninden API anahtarını al
    openai.api_key = os.getenv("OPEN_API_KEY")

    try:
        # OpenAI API'ye istek yapın
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Model adını belirtin
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant knowledgeable in cryptocurrency, including Bitcoin, Ethereum, and blockchain technology.",
                },
                {"role": "user", "content": content},
            ],
            max_tokens=500,  # Yanıtın maksimum uzunluğunu belirtin
        )

        # Yanıtı alın
        answer = response.choices[0].message["content"]
        print(answer)
        return answer

    except Exception as e:
        print(f"Hata: {e}")
        return None


def mail_send(why_send, site_name=None, content=None):
    # .env dosyasını yükle
    load_dotenv()

    # Gönderici ve alıcı e-posta adresleri
    gonderici_email = os.getenv("GONDERICI_MAIL")
    sifre = os.getenv("GONDERICI_MAIL_PASSWORD")
    alici_email = os.getenv("ALICI_MAIL")

    konu = ""
    mesaj_icerik = ""

    if why_send == "content_name":
        # E-posta içeriği
        konu = "Icerige ulasilamadi"
        mesaj_icerik = "İlk site içeriği alınamıyor"

    elif why_send == "content_for_ai":
        # E-posta içeriği
        konu = "Icerige ulasilamadi"
        mesaj_icerik = (
            site_name
            + " sitesinin "
            + content
            + " adindaki haberinin icerigine ulasilamadi."
        )

    elif why_send == "content_names_control":
        # E-posta içeriği
        konu = "Icerige ulasilamadi"
        mesaj_icerik = (
            content
            + " adındaki içerik kayıt edilme komutu verilmesine rağmen kayıt edilememiştir."
        )

    # MIMEMultipart nesnesi oluştur ve başlık bilgilerini ekle
    mesaj = MIMEMultipart()
    mesaj["From"] = gonderici_email
    mesaj["To"] = alici_email
    mesaj["Subject"] = konu

    # Mesaj içeriğini ekle
    mesaj.attach(MIMEText(mesaj_icerik, "plain"))

    try:
        # Gmail SMTP sunucusuna bağlan
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()  # Güvenli bağlantı başlat
        server.login(gonderici_email, sifre)  # Hesaba giriş yap

        # E-postayı gönder
        server.send_message(mesaj)
        print("E-posta başarıyla gönderildi!")

        # Bağlantıyı kapat
        server.quit()

    except Exception as e:
        print(f"E-posta gönderimi sırasında hata oluştu: {e}")


def save_to_json(answer, writer, title):
    try:
        # JSON dosyasını okumaya çalış, yoksa boş bir liste oluştur
        try:
            with open("ai_responses.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        # Yeni veriyi hazırla
        new_entry = {
            "timestamp": datetime.now().isoformat(),
            "writer": writer,
            "title": title,
            "ai_response": answer,
        }

        # Veriyi listeye ekle
        data.append(new_entry)

        # JSON dosyasına kaydet
        with open("ai_responses.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print("AI yanıtı JSON dosyasına kaydedildi")
    except Exception as e:
        print(f"JSON kaydetme hatası: {e}")


def process_content(content_for_AI, writer, onelink):
    if content_for_AI:
        print(content_for_AI.text)
        answer_ai = send_to_ai(content_for_AI.text)
        save_to_json(answer_ai, writer, onelink.text)
        print(answer_ai)
    else:
        print("Belirtilen öğe bulunamadı.")
        mail_send(why_send="content_for_ai", site_name=writer, content=onelink.text)


def main():
    # ChromeDriver'ı otomatik yönetim ile başlat
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    # Hedef URL'yi aç
    url = "https://tr.investing.com/news/cryptocurrency-news"
    driver.get(url)

    # Sayfanın tam olarak yüklenmesi için bekleme süresi
    time.sleep(5)

    # Sayfanın HTML kaynağını alın
    html_content = driver.page_source

    # BeautifulSoup ile HTML'yi parse et
    soup = BeautifulSoup(html_content, "html.parser")

    i = 0
    while True:
        try:
            # İlk haberi seçelim
            onelink = soup.find_all(
                "a",
                class_="text-inv-blue-500 hover:text-inv-blue-500 hover:underline focus:text-inv-blue-500 focus:underline whitespace-normal text-sm font-bold leading-5 !text-[#181C21] sm:text-base sm:leading-6 lg:text-lg lg:leading-7",
            )[i]

            # Yazar kontrol
            writer = soup.find_all("span", class_="shrink-0 text-xs leading-4")[i]

            if (
                writer.text == "Investing.com"
                or writer.text == "Foreks"
                or writer.text == "Coin Mühendisi"
            ):
                i += 1  # Bir sonraki habere geç
                continue  # Döngünün başına dön

            # Kayıt dosyası okuma
            with open("content_names.txt", "r+", encoding="utf-8") as file:
                # Dosyadaki içeriği satır satır oku
                row_count = file.readlines()

                # Dosyadaki içeriği tek bir string olarak al (satırlardaki \n'leri dahil et)
                file_content = "".join(row_count)

                if onelink.text not in file_content:
                    # 5 satırı geçerse, en alt satırı sil ve yeni satırı ekle
                    if len(row_count) >= 5:
                        row_count.pop()  # Son satırı sil

                    # Dosyanın başına onelink değerini ve bir satır sonu ekle
                    row_count.insert(0, onelink.text + "\n")  # onelink'i en başa ekle

                    # Dosyayı baştan yazarak güncelle
                    file.seek(0)  # Dosyanın başına git
                    file.writelines(row_count)  # Güncellenmiş satırları yaz

                    # Kayıtlı olup olmadığını kontrol et
                    file.seek(0)  # Dosyanın başına git
                    file_content = file.read()  # Dosyayı yeniden oku
                    if onelink.text in file_content:

                        # İlk gidilecek link kontrolü
                        if onelink:

                            print(onelink.text)  # Linkin görünen metnini al

                            # Selenium ile ilgili linki bul ve tıkla
                            element_to_click = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.LINK_TEXT, onelink.text))
                            )
                            element_to_click.click()

                            # Yeni sayfanın tam yüklenmesini bekleyin
                            time.sleep(5)

                            # Yeni sayfanın HTML kaynağını alın
                            new_html_content = driver.page_source
                            new_soup = BeautifulSoup(new_html_content, "html.parser")

                            # "Devamını oku" bağlantısını bulalım
                            continue_to_read = new_soup.find(
                                "a",
                                class_="text-inv-blue-500 hover:text-inv-blue-500 hover:underline focus:text-inv-blue-500 focus:underline mt-3.5 flex items-center text-xs text-inv-blue-500",
                            )

                            if continue_to_read:
                                print(
                                    continue_to_read.text
                                )  # Linkin görünen metnini al

                                # href özniteliğini al
                                if continue_to_read and continue_to_read.has_attr(
                                    "href"
                                ):
                                    href_value = continue_to_read["href"]
                                    print("Href: ", href_value)
                                else:
                                    print("Href bulunamadı.")

                                # "Devamını oku" linkine tıkla
                                WebDriverWait(driver, 10).until(
                                    EC.element_to_be_clickable(
                                        (By.LINK_TEXT, continue_to_read.text)
                                    )
                                ).click()

                                # Tıklanan sayfanın yüklenmesini bekleyin
                                time.sleep(10)

                                driver.get(href_value)

                            # Yeni sayfanın HTML kaynağını alın
                            final_html_content = driver.page_source
                            final_soup = BeautifulSoup(
                                final_html_content, "html.parser"
                            )

                        else:
                            print("İlgili bağlantı bulunamadı.")
                            # WebDriver'ı kapat
                            driver.quit()
                            return  # Fonksiyondan çık ve devam eden kodları çalıştırma

                        if writer.text == "Bitcoin Sistemi":
                            print("Bitcoin Sistemi")

                            # content_for_AI'nin gerçekten var olup olmadığını kontrol edin
                            content_for_AI = final_soup.find(
                                "div",
                                class_="tdb-block-inner td-fix-index",
                            )

                            process_content(content_for_AI, writer, onelink)
                            break

                        elif writer.text == "Kripto Piyasasi":
                            print("Kripto Piyasasi")

                            # content_for_AI'nin gerçekten var olup olmadığını kontrol edin
                            content_for_AI = final_soup.find(
                                "div",
                                class_="td_block_wrap tdb_single_content tdi_49 td-pb-border-top td_block_template_9 td-post-content tagdiv-type",
                            )

                            process_content(content_for_AI, writer, onelink)
                            break

                        elif writer.text == "BTC haber":
                            print("BTC haber")

                            # content_for_AI'nin gerçekten var olup olmadığını kontrol edin
                            content_for_AI = final_soup.find(
                                "div",
                                class_="entry-content pt-2",
                            )

                            process_content(content_for_AI, writer, onelink)
                            break

                        elif writer.text == "CoinTurk":
                            print("CoinTurk")

                            # content_for_AI'nin gerçekten var olup olmadığını kontrol edin
                            content_for_AI = final_soup.find(
                                "div",
                                class_="entry-content rbct clearfix is-highlight-shares",
                            )

                            process_content(content_for_AI, writer, onelink)
                            break

                        elif writer.text == "CoinKolik":
                            print("CoinKolik")

                            # content_for_AI'nin gerçekten var olup olmadığını kontrol edin
                            content_for_AI = final_soup.find(
                                "div", class_="entry-content pt-4"
                            )

                            process_content(content_for_AI, writer, onelink)
                            break

                        elif writer.text == "KoinMedya":
                            print("KoinMedya")

                            # content_for_AI'nin gerçekten var olup olmadığını kontrol edin
                            content_for_AI = final_soup.find(
                                "div", class_="entry-content-inner"
                            )

                            process_content(content_for_AI, writer, onelink)
                            break

                        elif writer.text == "koinbulteni":
                            print("koinbulteni")

                            # content_for_AI'nin gerçekten var olup olmadığını kontrol edin
                            content_for_AI = final_soup.find(
                                "div",
                                class_="post_content post_content_single entry-content",
                            )

                            process_content(content_for_AI, writer, onelink)
                            break

                        elif writer.text == "Gazete Banka":
                            print("Gazete Banka")

                            # content_for_AI'nin gerçekten var olup olmadığını kontrol edin
                            content_for_AI = final_soup.find(
                                "div", class_="entry-content-inner"
                            )

                            process_content(content_for_AI, writer, onelink)
                            break

                        elif writer.text == "CoinOtag":
                            print("CoinOtag")

                            # content_for_AI'nin gerçekten var olup olmadığını kontrol edin
                            content_for_AI = final_soup.find(
                                "div",
                                class_="td_block_wrap tdb_single_content tdi_71 td-pb-border-top td_block_template_1 td-post-content tagdiv-type",
                            )

                            process_content(content_for_AI, writer, onelink)
                            break

                        elif writer.text == "T24":
                            print("T24")

                            # content_for_AI'nin gerçekten var olup olmadığını kontrol edin
                            content_for_AI = final_soup.find(
                                "div",
                                class_="_3QVZl",
                            )

                            process_content(content_for_AI, writer, onelink)
                            break

                        elif writer.text == "koinbulteni":
                            print("koinbulteni")

                            # content_for_AI'nin gerçekten var olup olmadığını kontrol edin
                            content_for_AI = final_soup.find(
                                "div",
                                class_="post_content post_content_single entry-content",
                            )

                            process_content(content_for_AI, writer, onelink)
                            break

                        elif writer.text == "CoinDesk Türkiye":
                            print("CoinDesk Türkiye")

                            # content_for_AI'nin gerçekten var olup olmadığını kontrol edin
                            content_for_AI = final_soup.find(
                                "div",
                                class_="detail-content css-16v5xpg",
                            )

                            process_content(content_for_AI, writer, onelink)
                            break

                        elif writer.text == "Uzmancoin":
                            print("Uzmancoin")
                            content_for_AI = final_soup.find(
                                "div",
                                class_="post-body xt-post-content",
                            )
                            process_content(content_for_AI, writer, onelink)
                            break

                        else:
                            print("esit degil")

                        # WebDriver'ı kapat
                        driver.quit()

                    else:
                        mail_send(
                            why_send="content_names_control", content=onelink.text
                        )

                else:
                    print("content_names dosyasının içeriği ile aynı.")
                    driver.quit()
                    break  # İşlem tamamlandıktan sonra döngüden çık

        except IndexError:
            print("Kontrol edilecek başka haber kalmadı.")
            break

        except Exception as e:
            print(f"Bir hata oluştu: {e}")
            mail_send(why_send="content_name")
            break


while True:
    main()
    time.sleep(300)
