import streamlit as st
from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter, Language, MarkdownHeaderTextSplitter, MarkdownTextSplitter
import tiktoken
import markdownify
from bs4 import BeautifulSoup


# Streamlit UI
st.title("Text Splitter Playground")
st.info("""Split a text into chunks using a **Text Splitter**. Parameters include:

- `chunk_size`: Max size of the resulting chunks (in either characters or tokens, as selected)
- `chunk_overlap`: Overlap between the resulting chunks (in either characters or tokens, as selected)
- `length_function`: How to measure lengths of chunks, examples are included for either characters or tokens
- The type of the text splitter, this largely controls the separators used to split on
""")
col1, col2, col3, col4 = st.columns([1, 1, 1, 2])

with col1:
    chunk_size = st.number_input(min_value=1, label="Chunk Size", value=1000)

with col2:
    # Setting the max value of chunk_overlap based on chunk_size
    chunk_overlap = st.number_input(
        min_value=0,
        max_value=chunk_size - 1,
        label="Chunk Overlap",
        value=int(chunk_size * 0.2),
    )

    # Display a warning if chunk_overlap is not less than chunk_size
    if chunk_overlap >= chunk_size:
        st.warning("Chunk Overlap should be less than Chunk Length!")

with col3:
    length_function = st.selectbox(
        "Length Function", ["Characters", "Tokens"]
    )

splitter_choices = ["RecursiveCharacter", "Character", "MarkdownTextSplitter", "MarkdownHeaderTextSplitter"] + [str(v) for v in Language]

with col4:
    splitter_choice = st.selectbox(
        "Text Splitter", splitter_choices
    )

if length_function == "Characters":
    length_function = len
elif length_function == "Tokens":
    enc = tiktoken.get_encoding("cl100k_base")


    def length_function(text: str) -> int:
        return len(enc.encode(text))

else:
    raise ValueError

# Box for pasting text
doc = st.text_area("Paste Source Text")

# Data preprocessing
col5, col6 = st.columns([3, 1], vertical_alignment="bottom", )
with col5:
    page_build_system = st.selectbox("Page Build System", ["None", "Gatsby", "DocC", "DocFX", "dokka", "dart doc", "Sphinx"])

    page_soup = BeautifulSoup(doc, "html.parser")
    
    if page_build_system == "Gatsby":
        article = page_soup.find(id="main")
        sidebar_container = article.find(class_="sidebar-container")
        sidebar_container.extract()

        for tab_nav in article.find_all(class_="tab-nav"):
            buttons = []
            for button in tab_nav.find_all("button"):
                buttons.append(f"###### {button.text}")
                button.extract()
            tab_div = tab_nav.parent
            tab_contents = []
            open_tab_content = tab_div.find(class_="tab-content block")
            tab_contents.append(open_tab_content)
            open_tab_content.extract()
            for tab_content in tab_div.find_all(class_="tab-content hidden"):
                tab_contents.append(tab_content)
                tab_content.extract()
            if len(buttons) != len(tab_contents):
                continue
            # Rebuild linearly.
            for i in range(0, len(buttons)):
                tab_div.append(buttons[i])
                tab_div.append(tab_contents[i])  
                
        for tooltip in article.find_all("calcite-tooltip"):
            tooltip.extract()
        for calcite_button in article.find_all("calcite-button"):
            calcite_button.extract()
        for calcite_dropdown in article.find_all("calcite-dropdown"):
            calcite_dropdown.extract()
        for button in article.find_all("button"):
            button_id = button.get("id", "")
            # Account for accordions - they have important text on the buttons.
            if not button_id or "AccordionItem-" not in button_id:
                button.extract()
        for image in article.find_all("img"):
            image.extract()
        for iframe in article.find_all("iframe"):
            iframe.extract()
        for line_number in article.find_all(class_="react-syntax-highlighter-line-number"):
            line_number.extract()

        # Indicate diff.
        for code_line in article.find_all("span", attrs={"style": "--code-line-bg:var(--color-code-line-added-background);--line-number-digits:-1rem"}):
            code_line.replace_with(f"🟢{code_line.text}")
        for code_line in article.find_all("span", attrs={"style": "--code-line-bg:var(--color-code-line-removed-background);--line-number-digits:-1rem"}):
            code_line.replace_with(f"🔴{code_line.text}")
        for code_line in article.find_all("span", attrs={"style": "--code-line-bg:var(--color-code-line-changed-background);--line-number-digits:-1rem"}):
            code_line.replace_with(f"🟡{code_line.text}")

        for a in article.find_all("a", href=True):
            a.attrs.pop("href", None)
        for card in article.find_all(class_="card"):
            card.extract()
        
        for svg in article.find_all("svg"):
            aria_label = svg.get("aria-label", "")
            if aria_label:
                match aria_label:
                    case "Supported":
                        svg.replace_with("✅")
                    case "Not Supported":
                        svg.replace_with("❌")
                    case "Partially Supported (see notes)":
                        svg.replace_with("⚠️")
        
        for calcite_icon in article.find_all("calcite-icon"):
            aria_label = calcite_icon.get("aria-label", "")
            if aria_label:
                match aria_label:
                    case "Warning":
                        calcite_icon.replace_with("⚠️")
                    case "Note":
                        calcite_icon.replace_with("ℹ️")
                    case "Tip":
                        calcite_icon.replace_with("ℹ️")
                    case "Attention":
                        calcite_icon.replace_with("❗")
                    case "Topic":
                        calcite_icon.replace_with("📖")

        doc = str(article).replace("Go to tutorial", "")

    elif page_build_system == "DocC":
        article = page_soup.find(id="app-main")
        for wbr in article.find_all("wbr"):
            wbr.extract()
        for a in article.find_all("a", href=True):
            a.attrs.pop("href", None)
        doc = str(article)

    elif page_build_system == "DocFX":
        article = page_soup.find(id="_content")
        for wbr in article.find_all("wbr"):
            wbr.extract()
        for a in article.find_all("a", href=True):
            a.attrs.pop("href", None)
        doc = str(article)

    elif page_build_system == "dokka":
        article = page_soup.find(id="main")
        for a in article.find_all("a", href=True):
            a.attrs.pop("href", None)
        doc = str(article)

    elif page_build_system == "dart doc":
        article = page_soup.find(id="dartdoc-main-content")
        for a in article.find_all("a", href=True):
            a.attrs.pop("href", None)
        doc = str(article)

    elif page_build_system == "Sphinx":
        article = page_soup.find(class_="document")
        for header_link in article.find_all(class_="headerlink"):
            header_link.extract()
        for a in article.find_all("a", href=True):
            a.attrs.pop("href", None)
        doc = str(article)

with col6:
    if(st.button("Markdownify Text")):
        doc = markdownify.markdownify(doc)

st.markdown(doc)

# Choose splitter
if splitter_choice == "Character":
    splitter = CharacterTextSplitter(separator = "\n\n",
                                    chunk_size=chunk_size, 
                                    chunk_overlap=chunk_overlap,
                                    length_function=length_function)
elif splitter_choice == "RecursiveCharacter":
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, 
                                            chunk_overlap=chunk_overlap,
                                    length_function=length_function)
elif "Language." in splitter_choice:
    language = splitter_choice.split(".")[1].lower()
    splitter = RecursiveCharacterTextSplitter.from_language(language,
                                                            chunk_size=chunk_size,
                                                            chunk_overlap=chunk_overlap,
                                    length_function=length_function)
elif "MarkdownHeaderText" in splitter_choice:
    splitter = MarkdownHeaderTextSplitter(
        [("#", "Header 1"),
         ("##", "Header 2"),
         ("###", "Header 3"),
         ("####", "Header 4"),
         ("#####", "Header 5"),
         ("######", "Header 6")],
        strip_headers=False)
elif "MarkdownText" in splitter_choice:
    splitter = MarkdownTextSplitter(chunk_size=chunk_size,
                                   chunk_overlap=chunk_overlap,
                                   length_function=length_function)
else:
    raise ValueError

# Split the text
if doc != "":
    splits = splitter.split_text(doc)

    if "MarkdownHeaderText" in splitter_choice:
        new_splits = []
        for split in splits:
            new_split = split.page_content
            new_splits.append(new_split)
        splits = new_splits
        
    # Display the splits
    for idx, split in enumerate(splits, start=1):
        st.text_area(
            f"Split {idx}", split, height=200
        ) 