from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.PDF import PDF
from RPA.Archive import Archive
from RPA.Tables import Tables
from time import sleep


@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    browser.configure(slowmo=0, headless=False)
    download_orders_csv()
    orders = get_orders()

    open_robot_order_website()

    for order in orders:
        close_annoying_modal()
        process_order(order)
        browser.page().click('#order-another')

    archive = Archive()
    archive.archive_folder_with_zip('output/receipts', 'output/receipts.zip')


def download_orders_csv():
    """Downloads the CSV file from RobotSpareBin Industries"""
    http = HTTP()
    http.download("https://robotsparebinindustries.com/orders.csv",
                  target_file="orders.csv", overwrite=True)


def get_orders():
    """Read the downloaded CSV file and return it in a normalized format"""
    csv = Tables()

    orders = csv.read_table_from_csv("orders.csv")
    csv.rename_table_columns(
        orders, ["order_number", "head", "body", "legs", "address"])

    return orders


def open_robot_order_website():
    """Navigates to the RobotSpareBin Industries Inc. order page"""
    browser.goto("https://robotsparebinindustries.com/#/robot-order")


def close_annoying_modal():
    page = browser.page()
    page.click("button:text('Yep')")


def process_order(order):
    page = browser.page()
    page.select_option('#head', order['head'])
    body = order['body']
    page.click(f'#id-body-{body}')
    page.fill(
        "input[placeholder='Enter the part number for the legs']", order['legs'])
    page.fill('#address', order['address'])

    while not page.is_visible('#receipt'):
        page.click('#order')

    order_number = order['order_number']
    preview_image = f'output/{order_number}.png'

    receipt = page.locator('#receipt').inner_html()
    page.locator('#robot-preview-image').screenshot(path=preview_image)

    output_path = f'output/receipts/order-{order_number}.pdf'

    pdf = PDF()
    pdf.html_to_pdf(receipt, output_path)
    pdf.add_files_to_pdf(
        files=[output_path, preview_image],
        target_document=output_path
    )

    return {
        receipt,
        preview_image
    }
