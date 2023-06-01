from enum import Enum
import constants
# NOTE: Filter the text based on whether the text contains certain keywords
# True mean include, False means exclude

def filterByKeywords(contents: list[str], keywords: list[str]) -> list[bool]:
    decisions: list[bool] = []
    for content in contents:
        decision = False
        for keyword in keywords:
            if keyword.isspace():
                continue
            if keyword.lower() in content.lower():
                decision = True
                break
        decisions.append(decision)
    return decisions

# Filter by voting
def applyDecisions(contents: list[str], *decisionsList: list[bool], method=constants.VotingDecision.YES_ONE) -> list[str]:
    ret: list[str] = []
    for index, content in enumerate(contents):
        decisions = [row[index] for row in decisionsList]
        if reduceDecisions(decisions, method):
            ret.append(content)
    return ret

def reduceDecisions(decisions: list[bool], method=constants.VotingDecision.YES_ONE) -> bool:
    if method == constants.VotingDecision.YES_ONE:
        for decision in decisions:
            if decision:
                return True
    
    if method == constants.VotingDecision.ALL:
        for decision in decisions:
            if decision is False:
                return False
        return True
    
    if method == constants.VotingDecision.MAJORITY:
        return decisions.count(True) / len(decisions)  * 100 > 50
    
    return False