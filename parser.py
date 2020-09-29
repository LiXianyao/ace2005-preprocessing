#-*-encoding:utf8-*-#
from xml.etree import ElementTree
from bs4 import BeautifulSoup
import nltk
import json
from utils import removeNextLineAndSpace, calculateSkipPos, findNext
import re


class Parser:
    def __init__(self, path, withValue):
        self.path = path
        self.entity_mentions = []
        self.event_mentions = []
        self.sentences = []
        self.withValue = withValue
        print("ACE Value and Time are include?: {}".format(withValue))
        self.sgm_text = ''
        self.remove_list = []

        self.sents_with_pos = self.parse_sgm(path + '.sgm')
        self.entity_mentions, self.event_mentions = self.parse_xml(path + '.apf.xml')
        self.fix_wrong_position()

    @staticmethod
    def clean_text(text):
        return text.replace('\n', ' ')

    def get_data(self):
        data = []
        for sent in self.sents_with_pos:
            item = dict()

            item['sentence'] = self.clean_text(sent['text'])
            item['position'] = sent['position']
            text_position = sent['position']

            item['sentence'] = item['sentence'].strip()

            entity_map = dict()
            item['golden-entity-mentions'] = []
            item['golden-event-mentions'] = []

            for entity_mention in self.entity_mentions:
                entity_position = entity_mention['position']
                if text_position[0] <= entity_position[0] and entity_position[1] <= text_position[1]:
                    item['golden-entity-mentions'].append({
                        'text': self.clean_text(entity_mention['text']),
                        'position': entity_position,
                        'entity-type': entity_mention['entity-type']
                    })
                    entity_map[entity_mention['entity-id']] = entity_mention

            for event_mention in self.event_mentions:
                event_position = event_mention['trigger']['position']
                if text_position[0] <= event_position[0] and event_position[1] <= text_position[1]:
                    event_arguments = []
                    for argument in event_mention['arguments']:
                        try:
                            entity_type = entity_map[argument['entity-id']]['entity-type']
                        except KeyError:
                            print('[Warning] The entity in the other sentence is mentioned. This argument will be ignored.')
                            continue

                        event_arguments.append({
                            'role': argument['role'],
                            'position': argument['position'],
                            'entity-type': entity_type,
                            'text': self.clean_text(argument['text']),
                        })

                    item['golden-event-mentions'].append({
                        'trigger': event_mention['trigger'],
                        'arguments': event_arguments,
                        'position': event_position,
                        'event_type': event_mention['event_type'],
                    })
            data.append(item)
        return data

    def find_correct_offset(self, sgm_text, start_index, text):
        offset = 0
        for i in range(0, 70):
            for j in [-1, 1]:
                offset = i * j
                if sgm_text[start_index + offset:start_index + offset + len(text)] == text:
                    return offset

        print('[Warning] fail to find offset! (start_index: {}, text: {}, path: {})'.format(start_index, text, self.path))
        return 0

    def fix_wrong_position(self):
        for entity_mention in self.entity_mentions:
            offset = self.find_correct_offset(
                sgm_text=self.sgm_text,
                start_index=entity_mention['position'][0],
                text=entity_mention['text'])

            entity_mention['position'][0] += offset
            entity_mention['position'][1] += offset

        for event_mention in self.event_mentions:
            offset1 = self.find_correct_offset(
                sgm_text=self.sgm_text,
                start_index=event_mention['trigger']['position'][0],
                text=event_mention['trigger']['text'])
            event_mention['trigger']['position'][0] += offset1
            event_mention['trigger']['position'][1] += offset1

            for argument in event_mention['arguments']:
                offset2 = self.find_correct_offset(
                    sgm_text=self.sgm_text,
                    start_index=argument['position'][0],
                    text=argument['text'])
                argument['position'][0] += offset2
                argument['position'][1] += offset2

    def parse_sgm(self, sgm_path):
        with open(sgm_path, 'r') as f:
            soup = BeautifulSoup(f.read(), features='html.parser')
            self.sgm_text = soup.text

            doc_type = soup.doc.doctype.text.strip()

            def remove_tags(selector):
                tags = soup.findAll(selector)
                for tag in tags:
                    tag.extract()

            remove_tags('datetime')
            if doc_type == 'WEB TEXT':
                remove_tags('poster')
                remove_tags('postdate')
                remove_tags('subject')
            elif doc_type in ['CONVERSATION', 'STORY']:
                remove_tags('speaker')

            try:
                remove_tags('headline')
                remove_tags('endtime')
            except:
                pass


            sents = []
            converted_text = soup.text

            for sent in self.sent_tokenize(converted_text):
                sents.extend(sent.split('\n\n'))
            sents = list(filter(lambda x: len(x) > 5, sents))
            sents = sents[1:]
            sents_with_pos = []
            last_pos = 0

            for sent in sents:
                pos = self.sgm_text.find(sent, last_pos)
                last_pos = pos

                usedPos = len(self.remove_list)
                cleanText, remove_idxs = removeNextLineAndSpace(sent, sgmPos=pos)
                self.remove_list.extend(remove_idxs)

                startPos = calculateSkipPos(self.remove_list[usedPos:], pos)
                endPos = calculateSkipPos(self.remove_list[usedPos:], pos + len(sent))
                print(len(cleanText))
                assert endPos - startPos == len(cleanText)

                self.sgm_text = self.sgm_text[:pos] + cleanText + self.sgm_text[pos + len(sent):]

                sents_with_pos.append({
                    'text': cleanText,
                    'position': [startPos, endPos]
                })

            return sents_with_pos

    def sent_tokenize(self, sent):
        idx = findNext(sent, pos=0, delimiters=["。", "！", "……"])
        last_idx = 0

        while idx != -1:
            yield sent[last_idx: idx + 1]
            last_idx = idx + 1
            idx = findNext(sent, pos=idx + 1, delimiters=["。", "！", "……"])
        yield sent[last_idx:]


    def parse_xml(self, xml_path):
        entity_mentions, event_mentions = [], []
        tree = ElementTree.parse(xml_path)
        root = tree.getroot()

        for child in root[0]:
            if child.tag == 'entity':
                entity_mentions.extend(self.parse_entity_tag(child))
            elif self.withValue and child.tag in ['value', 'timex2']:
                entity_mentions.extend(self.parse_value_timex_tag(child))
            elif child.tag == 'event':
                event_mentions.extend(self.parse_event_tag(child))

        return entity_mentions, event_mentions

    def parse_entity_tag(self, node):
        entity_mentions = []

        for child in node:
            if child.tag != 'entity_mention':
                continue
            extent = child[0]
            charset = extent[0]

            entity_mention = dict()
            entity_mention['entity-id'] = child.attrib['ID']
            entity_mention['entity-type'] = '{}:{}'.format(node.attrib['TYPE'], node.attrib['SUBTYPE'])
            cleanText, _ = removeNextLineAndSpace(charset.text, 0)
            entity_mention['text'] = cleanText

            startPos = calculateSkipPos(self.remove_list, int(charset.attrib['START']))
            endPos = calculateSkipPos(self.remove_list, int(charset.attrib['END']))
            entity_mention['position'] = [startPos, endPos]

            entity_mentions.append(entity_mention)

        return entity_mentions


    def parse_event_tag(self, node):
        event_mentions = []
        for child in node:
            if child.tag == 'event_mention':
                event_mention = dict()
                event_mention['event_type'] = '{}:{}'.format(node.attrib['TYPE'], node.attrib['SUBTYPE'])
                event_mention['arguments'] = []
                for child2 in child:
                    def removeUnused(charset):
                        cleanText, _ = removeNextLineAndSpace(charset.text, 0)
                        startPos = calculateSkipPos(self.remove_list, int(charset.attrib['START']))
                        endPos = calculateSkipPos(self.remove_list, int(charset.attrib['END']))
                        return cleanText, startPos, endPos

                    if child2.tag == 'ldc_scope':
                        charset = child2[0]
                        cleanText, startPos, endPos = removeUnused(charset)
                        event_mention['text'] = cleanText
                        event_mention['position'] = [startPos, endPos]
                    elif child2.tag == 'anchor':
                        charset = child2[0]
                        cleanText, startPos, endPos = removeUnused(charset)
                        event_mention['trigger'] = {
                            'text': cleanText,
                            'position': [startPos, endPos],
                        }
                    elif child2.tag == 'event_mention_argument':
                        extent = child2[0]
                        charset = extent[0]
                        cleanText, startPos, endPos = removeUnused(charset)
                        event_mention['arguments'].append({
                            'text': cleanText,
                            'position': [startPos, endPos],
                            'role': child2.attrib['ROLE'],
                            'entity-id': child2.attrib['REFID'],
                        })
                event_mentions.append(event_mention)
        return event_mentions


    def parse_value_timex_tag(self, node):
        entity_mentions = []

        for child in node:
            extent = child[0]
            charset = extent[0]

            entity_mention = dict()
            entity_mention['entity-id'] = child.attrib['ID']

            if 'TYPE' in node.attrib:
                entity_mention['entity-type'] = node.attrib['TYPE']
            if 'SUBTYPE' in node.attrib:
                entity_mention['entity-type'] += ':{}'.format(node.attrib['SUBTYPE'])
            if child.tag == 'timex2_mention':
                entity_mention['entity-type'] = 'TIM:time'

            cleanText, _ = removeNextLineAndSpace(charset.text, 0)
            entity_mention['text'] = cleanText

            startPos = calculateSkipPos(self.remove_list, int(charset.attrib['START']))
            endPos = calculateSkipPos(self.remove_list, int(charset.attrib['END']))
            entity_mention['position'] = [startPos, endPos]

            entity_mentions.append(entity_mention)

        return entity_mentions


if __name__ == '__main__':
    # parser = Parser('./data/ace_2005_td_v7/data/English/un/fp2/alt.gossip.celebrities_20041118.2331')
    parser = Parser('./data/ace_2005_td_v7/data/Chinese/bn/adj/CTS20001206.1300.0398', True)
    data = parser.get_data()
    with open('./output/debugC.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # index = parser.sgm_text.find("Diego Garcia")
    # print('index :', index)
    # print(parser.sgm_text[1918 - 30:])
