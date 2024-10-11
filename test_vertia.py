from playwright.sync_api import Page, expect
import random

# Specifikuje počet dluhopisů ke zakoupení
bond_quantity = 2

# Přihlašovací email
login_email = "test@vertia.com"

# Přihlašovací heslo
login_password = "_XL_1W_BVr"

# Website URL
website = "https://bond.vertia.cloud/"

"""
Test pro nákup dluhopisů na platformě Vertia

Provede se nákup dluhopisů ve specifikovaném množství.
Vybírá se vždy první dluhopis ze seznamu.
Pokud je nákup dluhopisu právě rozpracováno, dojde k vyvolání expectu, kdy text popup okna nesedí s názvem nakupovaného dluhopisu.

Pozor: Úkol krok č. 13 - Finální kontrola částky k zaplacení funguje za předpokladu, že daný vklad se řadí sestupně = aktuální vklad bude na první pozici.
       Aktuálně je seznam vkladů neseřazený a pravděpodobně náhodný = otevírá se špatný vklad po podpisu dokumentů.
       Možnost řešení je oprava na straně aplikace tak, aby byl seznam správně seřazený. Případně provést implementaci logiky testu, kdy dojde
       k nalezení posledního vkladu podle nejvyššího čísla "osobní účet".
"""
def test_vertia_buy_bonds(page: Page):
    page.goto(website)

    # Vyplnění emailu a hesla
    page.fill('input[type="email"]', login_email)
    page.fill('input[type="password"]', login_password)
        
    # Klik - tlačítko "Přihlásit se"
    page.locator("[class*='loginWindowContent'] button").nth(1).click()
 
    # Klik - nakoupit dluhopis
    page.click('div.svgIconContainer.investButton')  

    # První dluhopis z výběru
    first_product = page.locator('div.productItem').first

    bond_name = first_product.locator('h3').inner_text()
    bond_price = first_product.locator('div.productItemHighlightValue').nth(0).text_content()

    # Naformátovat př. 100 000 Kč = 100000
    bond_price_number = int(''.join(bond_price.split()[:-1]).replace(' ', ''))

    # Nastavení množství dluhopisu na 2
    first_product.locator('input[type="number"]').fill(str(bond_quantity))  

    # Klik - Nakoupit dluhopis
    first_product.locator('button').click()

    # Očekávám název dluhopisu v popup okně
    expect(page.locator('div.popup h3')).to_have_text(bond_name)

    # Klik - potvrdit nákup
    page.click('div.popup button')

    # Čeká se, dokud není dokument načtený
    page.wait_for_selector('div.react-pdf__Document') 

    # Posuneme se úplně dolů v tomto divu
    page.evaluate(
        """
        const div = document.querySelector('div.react-pdf__Document');
        div.scrollTop = div.scrollHeight;
        """)

    # Počkáme na dokončení scrollování 
    page.wait_for_timeout(1000) 

    # Uloží screenshot celé stránky včetně první smlouvy
    page.screenshot(path='screenshot_document1.png', full_page=True) 

    tabs = page.locator('div.documentTabs > div')
    tabs.nth(2).click()

    # Čeká se, dokud není dokument načtený
    page.wait_for_selector('div.react-pdf__Document')

    # Posuneme se úplně dolů v tomto divu
    page.evaluate(
        """
        const div = document.querySelector('div.react-pdf__Document');
        div.scrollTop = div.scrollHeight;
        """)

    # Počkáme na dokončení scrollování 
    page.wait_for_timeout(1000) 

    # Uloží screenshot celé stránky včetně druhé smlouvy
    page.screenshot(path='screenshot_document2.png', full_page=True)

    # Klik - podpis dokumentů
    page.locator('div.formLine button').nth(1).click()

    # Vytvoření náhodného čísla a vložení do inputu
    random_confirm_number = random.randint(100000, 999999)   
    confirm_number_input = page.locator('div.popupContainer input')
    confirm_number_input.fill(str(random_confirm_number))

    # Počkáme na dokončení vyplnění (zamezení občasné zaseknutí aplikace)
    page.wait_for_timeout(500) 

    final_price = page.locator('div.accordionLine.open div.flexLine.priceLine span').inner_text()
    final_price_number = convert_price_to_number(final_price)

    # Finální ověření, zdali výsledná cena sedí se zakoupenými dluhopisy
    assert bond_price_number * bond_quantity == final_price_number, 'Bond total price does not match final price'

def convert_price_to_number(price):
    cleaned_value = price.replace(u'\xa0', '').split(',')[0]
    return int(cleaned_value)  # Převod na celé číslo