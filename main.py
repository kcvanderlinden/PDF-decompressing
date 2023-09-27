# Created by Karel van der Linden - 2022

from operator import itemgetter
import fitz
import jellyfish
import pandas as pd

def pdf_to_dict(path):

    doc = fitz.open(path)

    font_counts, styles = fonts(doc, granularity=True)

    size_tag = font_tags(font_counts, styles, granularity=True)

    elements = headers_para(doc, size_tag)
    topscript_list = [elements.index(elem)+1 for elem in elements if elem['tag'] == '<p_break>'] # make list of first entries on page
    topscript_list.pop(-1) # remove last, because there is no topscript on the next page after the last page
    elements = pop_repeating(elements, topscript_list)
    endscript_list = [elements.index(elem)-1 for elem in elements if elem['tag'] == '<p_break>'] # make list of last entries on page
    elements = pop_repeating(elements, endscript_list)

    # primary_heading = deter_primary_h(elements)
    return elements

# functie om te controleren of value een nummer is.
def digitize(value): # NOT IN  USE
    try:
        float(value)
        return True
    except ValueError:
        return False

def relative_borderdistance(list_of_bboxes, x_page, y_page, whole_page=True): # set whole_page to false if use for 'spans'
    list_of_bboxlists = []
    entry_count = 0
    for box in list_of_bboxes:
        try:
            x_l_distance = round(box[0] / x_page, 3)
        except:
            print(box)
            print(list_of_bboxes)
        x_l_distance = round(box[0] / x_page, 3)
        x_r_distance = round(box[2] / x_page, 3)
        y_t_distance = round(box[1] / y_page, 3)
        y_b_distance = round(box[3] / y_page, 3)
        if whole_page:
            entry = [x_l_distance, y_t_distance, y_b_distance, x_r_distance, entry_count]
        else:
            entry = [y_t_distance, x_l_distance, y_b_distance, x_r_distance, entry_count]
        
        entry_count += 1
        list_of_bboxlists.append(entry)
    # EXPERIMENTAL: FIDDLING WITH COORDINATES TO ORGANIZE SCRAPED TEXT FROM PAGE
    if whole_page:
        for p in list_of_bboxlists:
            p[2] = p[0] * (p[1] ** 2)
    df_bboxes = pd.DataFrame(list_of_bboxlists) # matrix of coordinates to dataframe to sort it.
    df_bboxes_sorted = df_bboxes.sort_values(by = [2, 0, 1]) # --> volgorde voor uitlezen van pagina.
    # df_bboxes_sorted = df_bboxes.sort_values(by = [0, 1, 2, 3]) # UNCOMMENT FOR ORIGINAL SORTING
    # END EXPERIMENTAL

    bboxes_y_sorted = df_bboxes.sort_values(by = [2])[4].to_list()
    y_highest = bboxes_y_sorted[0]
    y_lowest = bboxes_y_sorted[-1]
    
    return df_bboxes_sorted[4].to_list(), y_highest, y_lowest

def fonts(doc, granularity):
    """Extracts fonts and their usage in PDF documents.

    :param doc: PDF document to iterate through
    :type doc: <class 'fitz.fitz.Document'>
    :param granularity: also use 'font', 'flags' and 'color' to discriminate text
    :type granularity: bool

    :rtype: [(font_size, count), (font_size, count}], dict
    :return: most used fonts sorted by count, font style information
    """
    styles = {}
    font_counts = {}

    for page in doc:
        blocks = page.get_text("dict", flags=11)["blocks"]
        for b in blocks:  # iterate through the text blocks
            if b['type'] == 0:  # block contains text
                for l in b["lines"]:  # iterate through the text lines
                    for s in l["spans"]:  # iterate through the text spans
                        if granularity:
                            identifier = f"{s['size']}_{s['flags']}_{s['font']}_{s['color']}"
                            styles[identifier] = {'size': s['size'], 'flags': s['flags'], 'font': s['font'],
                                                  'color': s['color']}
                            
                        else:
                            identifier = f"{s['size']}"
                            styles[identifier] = {'size': s['size'], 'font': s['font']}
                            
                        font_counts[identifier] = font_counts.get(identifier, 0) + 1  # count the fonts usage
    font_counts = sorted(font_counts.items(), key=itemgetter(1), reverse=True)
    if len(font_counts) < 1:
        raise ValueError("Zero discriminating fonts found!")
    #print(font_counts)
    #print(styles)
    return font_counts, styles


def font_tags(font_counts, styles, granularity):
    # kan veel simpeler, want ik weet wat paragraph style is, met eerste deel van de functie. \
    # Het enige wat er nog moet gebeuren is alles wat groter of vetter is, moet heading, alles wat kleiner is, moet subscript. 
    """Returns dictionary with font sizes as keys and tags as value.

    :param font_counts: (font_size, count) for all fonts occuring in document
    :type font_counts: list
    :param styles: all styles found in the document
    :type styles: dict

    :rtype: dict
    :return: all element tags based on font-sizes
    """
    p_style = styles[font_counts[0][0]]  # get style for most used font by count (paragraph)
    p_size = p_style['size']  # get the paragraph's size
    
    sort_on_size = dict(sorted(styles.items(), key = lambda x: x[1]['size'])) # sorting the font sizes low to high, so that we can append the right integer to each tag
    
    index_of_p = list(sort_on_size.keys()).index(font_counts[0][0])
    id_upper = 1
    id_lower = 1 
    app_tag = {}
    
    app_tag[font_counts[0][0]] = f"<p>"

    if index_of_p > 0: # whether there are smaller fonts in the document
        index_of_style = 0
        while index_of_style < index_of_p: # tag all smaller sizes in order from small to large untill index of paragraph
            app_tag[list(sort_on_size.keys())[index_of_style]] = f"<s{id_lower}>" #set subscript tags
            id_lower += 1
            index_of_style += 1
    index_of_style = index_of_p + 1
    while index_of_style < len(list(sort_on_size.keys())): # tag all larger sizes in order from small to large untill last entry in list
        app_tag[list(sort_on_size.keys())[index_of_style]] = f"<h{id_upper}>" #set subscript tags
        id_upper += 1
        index_of_style += 1

    '''# sorting the font sizes high to low, so that we can append the right integer to each tag
    font_appearances = []
    if granularity:
        font_appearances = [font_app for (font_app, count) in font_counts]
    else:
        font_appearances = [font_app for (font_app, count) in font_counts]
    font_appearances.sort(reverse=True)
    # aggregating the tags for each font size
    id_upper = 1
    id_lower = 1 
    app_tag = {}
    for app in font_appearances:
        # font_label = '-'.join(re.split('_', app)[0:2])
        font_size = styles[app]['size']
        if font_size == p_size and p_style == app:
            idx = 0
            app_tag[app] = "<p>"
        if font_size > p_size:
            app_tag[app] = f"<h{id_upper}>"
            id_upper += 1
        elif font_size < p_size:
            app_tag[app] = f"<s{id_lower}>"
            id_lower += 1'''
        
    return app_tag


def headers_para(doc, size_tag):
    """Scrapes headers & paragraphs from PDF and return texts with element tags.

    :param doc: PDF document to iterate through
    :type doc: <class 'fitz.fitz.Document'>
    :param size_tag: textual element tags for each size
    :type size_tag: dict

    :rtype: list
    :return: texts with pre-prended element tags
    """
    header_para = []  # list with headers and paragraphs
    first_span = True  # boolean operator for first span
    previous_s = {}  # previous span
    last_highest_or_lowest = {}
    page_num = 1
    t_point = 30 # amount of pixels/points that defines a white line is between two lines.

    for page in doc:
        previous_highest_or_lowest_on_page = False
        x_page = page.get_text("dict")['width'] # width of page
        y_page = page.get_text("dict")['height'] # height of page
        blocks = page.get_text("dict")["blocks"]
        list_of_bboxes_blocks = [block['bbox'] for block in blocks] # a list containing all the blocks on the page with the regarding coordinaties.
        if len(list_of_bboxes_blocks) > 0:
            bboxes_ordered, y_highest, y_lowest = relative_borderdistance(list_of_bboxes_blocks, x_page, y_page)
            for b in bboxes_ordered:
                if b == y_lowest: 
                    highest_or_lowest_on_page = True
                else:
                    highest_or_lowest_on_page = False
                block = blocks[b]
                # for b in blocks:  # iterate through the text blocks
                if block['type'] == 0:  # this block contains text+

                    # REMEMBER: multiple fonts and sizes are possible IN one block, wil ik dit? Of wil ik gewogen? 
                    # Hoe vaak kom je titel tegen met in dezelfde lijn paragraaf_text? functie is niet gearceerde woorden eruit te halen.

                    block_string = ""  # text found in block
                    list_of_bboxes_spans = [span['bbox'] for s in block["lines"] for span in s['spans']]
                    span_bboxes_ordered = relative_borderdistance(list_of_bboxes_spans, x_page, y_page, whole_page=False)[0]
                    block_spans = [span for s in block["lines"] for span in s['spans']] # iterate through the text lines and text spans
                    for ordered_s in span_bboxes_ordered:
                        s = block_spans[ordered_s]
                        font_label = f"{s['size']}_{s['flags']}_{s['font']}_{s['color']}"
                        f_tag = size_tag[font_label]
                        if first_span:
                            previous_s = s
                            first_span = False
                            block_string = {
                                'tag': f_tag, 
                                'text': s['text'].strip(),
                                'page_num': page_num,
                                'p_position_x': s['origin'][0], # TODO use bbox
                                'p_position_y': s['origin'][1], # TODO use bbox
                                'font_size': s['size']
                                }
                            header_para.append(block_string)
                        else:
                            previous_s = header_para[-1]
                            if f_tag == previous_s['tag'] and 0 <= s['origin'][1] - previous_s['p_position_y'] <= (t_point + previous_s['font_size']) and f_tag != '<p>':

                                last_entry = header_para[-1]
                                last_entry['text'] += f" {s['text'].strip()}" 
                                last_entry['p_position_x'] = s['origin'][0]
                                last_entry['p_position_y'] = s['origin'][1]

                                header_para[-1] = last_entry
                            
                            elif f_tag == previous_s['tag'] and f_tag == '<p>': # and highest_or_lowest_on_page == False and last_highest_or_lowest != previous_s:

                                last_entry = header_para[-1]
                                last_entry['text'] += f" {s['text'].strip()}" 
                                last_entry['p_position_x'] = s['origin'][0]
                                last_entry['p_position_y'] = s['origin'][1]

                                header_para[-1] = last_entry
                            
                            elif s['text'].strip() == '':
                                pass

                            else:
                                block_string = {
                                    'tag': f_tag, 
                                    'text': s['text'].strip(),
                                    'page_num': page_num,
                                    'p_position_x': s['origin'][0],
                                    'p_position_y': s['origin'][1],
                                    'font_size': s['size']
                                    }
                                header_para.append(block_string)
                        if highest_or_lowest_on_page:
                            last_highest_or_lowest = header_para[-1] # set var so that able to check whether previous is a highest or lowest block on the page.
                        else:
                            last_highest_or_lowest = {}
    
        # het toevoegen van een dictionary die het einde van de pagina aangeeft. Maakt het werken rondom begin en einde van pagian makkelijker.
        block_string = {
            'tag': '<p_break>', 
            'text': f'A physical page break on page {page_num}',
            'page_num': page_num,
            'p_position_x': 0,
            'p_position_y': 0,
            'font_size': 0
            }
        header_para.append(block_string)
        page_num += 1
    
    return header_para

def pop_repeating(elements, s_list): # based on list of first or last entries on page, deter if these entries are similair and thus a standard footer for example.
    sim_list = []
    for i in range(len(s_list)-1):
        a, b = s_list[i], s_list[i+1]
        str_dist = str_distance(a, b, elements)
        if str_dist >= 0.8:
            sim_list.extend([a, b])
    sim_list = list(set(sim_list))
    sim_list.sort(reverse=True)
    if len(sim_list) - len(s_list) <= 3:
        [elements.pop(i) for i in sim_list]
    return elements

def str_distance(a, b, elements):
    a = elements[a]['text']
    b = elements[b]['text']
    dist = jellyfish.jaro_distance(a, b)
    return dist

# beter om terug te zoeken vanaf <p> en alle hogere headings een plek geven.
def deter_primary_h(elements): # NOT OF MOST IMPORTANCE
    b = [elem['tag'] for elem in elements] # make list of only the tags
    b_ = []
    for i in range(len(b)-2): # walk through list for headings that is inbetween 2 paragraphs
        if b[i] == b[i+2] and b[i] == '<p>':
            b_.append(b[i+1])
    tag_amount = []
    
    for x in list(set(b_)):
        if x.startswith('<h'): # only keep headings
            d_tag_amoung = {
                'tag': x,
                'amount': b_.count(x) 
            }
            tag_amount.append(d_tag_amoung)
    tag_amount = sorted(tag_amount, key=lambda i: i['amount'], reverse=True)
    
    primary = tag_amount[0]['tag'] if len(tag_amount) > 0 else ''
    return primary