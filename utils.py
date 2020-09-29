def removeNextLineAndSpace(sent, sgmPos):
    last_idx = 0
    idx = findNext(sent, pos=0, delimiters=["\n", " "])
    cleanText = ''
    remove_idxs = []

    while idx != -1:
        if not isSpaceBetweenWords(sent, idx):
            remove_idxs.append(idx + sgmPos)
            cleanText += sent[last_idx: idx]
        else:
            cleanText += sent[last_idx: idx + 1]
        last_idx = idx + 1
        idx = findNext(sent, pos=idx + 1, delimiters=["\n", " "])
    cleanText += sent[last_idx:]
    return cleanText, remove_idxs


def findNext(sent, pos, delimiters):
    ans = []
    for c in delimiters:
        idx = sent.find(c, pos)
        if idx > -1:
            ans.append(idx)
    return min(ans) if len(ans) > 0 else -1

def isSpaceBetweenWords(sent, idx):
    if sent[idx] != ' ' or idx == 0:
        return False

    try:
        if isEnglish(sent[idx - 1]) and isEnglish(sent[idx + 1]):
            return True
    except:
        pass
    finally:
        return False

def isEnglish(character):
    return (character >= 'a' and character <= 'z') or \
           (character >= 'A' and character <= 'Z')


def calculateSkipPos(removeRecord, pos):
    skipOffset = 0
    for skipIdx in removeRecord:
        if skipIdx < pos:
            skipOffset += 1
        else:
            break
    return pos - skipOffset

