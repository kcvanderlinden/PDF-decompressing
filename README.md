# PDF decompressing
The aim is to be able to detect the paragraphs and headings in a PDF. This allows for a much cleaner input for pdf mining. 

## Why important?
Reading a PDF as a human is easy. An average PDF file logically represents the information visually. However, a PDF file is stored without structure. This becomes appearant when copy pasting a PDF file to a wordproccesor: headings are not always recognized, lines are broken and footers are also copied. This mess also translates to reading a PDF through most packages for PDF mining. This means that automation of text mining can produce weird text output form a PDF file, which has an impact on the accuracy of text analytics. 

A PDF file can contain multiple types of information. Some example of information types that can be found in a PDF are:
<ul>
  <li>Images</li>
  <li>Tables</li>
  <li>Graphs</li>
  <li>Headers</li>
  <li>Footers</li>
  <li>Paragraphs</li>
  <li>Lists</li>
</ul>

With this project I primarily focus on converting a PDF file to readable text with correct headings. The aim is to have a package that can generally translate a PDF to paragraphs, headings and a title. This means that the code needs to understand when a paragraph continues at the next page, removes standard text at the top and bottom of the text and understand the hierarchy of headings.

## How constructed?
Just human logic, no fancy machine/deep learning at this moment. Maybe I can inspire someone or be of service by producing a test sample for a model.
