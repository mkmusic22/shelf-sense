import flet

def main(page: flet.Page):
    page.title = "ShelfSense"
    page.fonts = {
        "Inter": "/fonts/inter.ttf"
    }

    title_page = flet.Text("ShelfSense - Your Local Grocery Tracker", size=26, weight=flet.FontWeight.BOLD, align=flet.Alignment.CENTER, text_align=flet.TextAlign.CENTER)


    container = flet.Container(
        content=title_page
    )
    page.add(container)

flet.run(main)