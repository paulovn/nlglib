from copy import deepcopy
import re

from nlg.structures import *
import nlg.aggregation as aggregation
import nlg.lexicalisation as lexicalisation
import nlg.realisation as realisation
import nlg.format as format


class LanguageGen:
    """LanguageGen class represents the NLG module used for realising plans."""
    
    def __init__(self):
        self.nlg = Nlg()

    def realise_plan(self, plan):
        return self.nlg.realise_plan(plan)

    def realise_world(self, world, state):
        faulty = 0
        for sensor, reading in world.items():
            if reading > 5:
                faulty += 1

        if 0 < faulty:
            text = '{} of the sensors report high vibrations in section a.\n'.format(faulty)
        else:
            text = 'All sensors report nominal values.\n'

        return text


class Context:
    def __init__(self, ontology=None):
        self.ontology = ontology
        self.referents = dict()
        self.last_referent = None


class REG:
    def __init__(self):
        pass

    def gre(self, referent, context):
        # can we use a pronoun?
        # actually, using a pronoun for the last ref can still be ambiguous :-)
#        if referent == context.last_referent:
#            return NP(Word('it', 'PRONOUN'))

        result = None

        if referent in context.referents:
            result = self._do_repeated_reference(referent, context)
        else:
            result = self._do_initial_reference(referent, context)
        return result

    def _do_initial_reference(self, referent, context):
        result = None

        # do we have information about the referent?
        try:
            onto = context.ontology
            if onto is None: print('GRE does not have ontology!')

            entity_type = onto.best_entity_type(':' + referent)
            result = NP(Word(entity_type, 'NOUN'))
            print('\t%s: type "%s"' % (referent, entity_type))
            # if the object is the only one in the domain, add 'the'
            distractors = onto.entities_of_type(':' + entity_type)
            print('\tdistractors: %s' % str(distractors))
            count = len(distractors)

            if count == 1:
                # save the RE without the determiner
                context.referents[referent] = (True, deepcopy(result))
                # this should really be done by simpleNLG...
                if entity_type[0] in "aeiouy":
                    result.spec = Word('an', 'DETERMINER')
                else:
                    result.spec = Word('a', 'DETERMINER')
            else:
                context.referents[referent] = (False, result)
                # else add the number to distinguish from others
                number = None
                tmp = re.search(r"([^0-9]+)([0-9]+)$", referent)
                if (tmp is not None):
                    number = tmp.group(2)

                if (number is not None):
                    result.add_complement(Word(number))
        except Exception as msg:
            # if we have no info, assume referent is not unique
            result = NP(Word(referent, 'NOUN'))
            context.referents[referent] = (False, result)
            print('GRE for "%s" failed : "%s"' % (referent, str(msg)))

        context.last_referent = referent
        return result

    def _do_repeated_reference(self, referent, context):
        result = None

        is_unique, re = context.referents[referent]
        if is_unique:
            result = deepcopy(re)
            result.spec = Word('the', 'DETERMINER')
        else:
            result = re
        return result

    def _count_type_instances(self, entity_type, object_map):
        count = 0
        for k, v in object_map.items():
            if v == entity_type: count += 1
        return count


class Nlg:
    def __init__(self):
        self.responses = dict()
        self.literals = dict()
        self.reg = REG()
        self._load_responses()
        self._load_literals()

    def _load_responses(self):
        self.responses['justify'] = ''
        self.responses['argument_against_label_IN'] = ''
        self.responses['argument_against_label_OUT'] = ''
        self.responses['argument_against_label_UNDEC'] = ''

    def _load_literals(self):
        self.literals['edinburgh_bridge_closed'] = \
            'Forth Road Bridge outside Edinburgh is closed'
        self.literals['kincardie_bridge_10'] = \
            'the maximum allowed weight on Kincardine Bridge is 10 tons'
        self.literals['vehicle_weight_15'] = \
            'the weight of the vehicle is 15 tons'
        self.literals['traffic_very_slow'] = \
            'the traffic is very slow'
        self.literals['traffic_slow'] = \
            'the traffic is slow'
        self.literals['forecast_old'] = \
            'the forecast is recent'
        self.literals['forecast_high_wind'] = \
            'the weather forecast indicates high winds'
        self.literals['forecast_high_snow'] = \
            'the weather forecast indicates high snow fall'
        self.literals['accident'] = \
            'an accident'
        self.literals['accident_on_bridge'] = \
            'an accident on the bridge'
        self.literals['stirling_shorter'] = \
            'going through Stirling is faster'
        self.literals['kincardine_shorter'] = \
            'going through Kincardine is faster'
        self.literals['kincardine_better'] = \
            'going through Kincardine is better'

        self.literals['can_Edinburgh_to_Stirling'] = \
            'you can go from Edinburgh to Stirling'
        self.literals['can_Edinburgh_to_Kincardine'] = \
            'you can go from Edinburgh to Kincardine'
        self.literals['can_Edinburgh_to_Perth'] = \
            'you can go from Edinburgh to Perth'
        self.literals['can_Stirling_to_Perth'] = \
            'you can go from Stirling to Perth'
        self.literals['can_Perth_to_Aberdeen'] = \
            'you can go from Perth to Aberdeen'
        self.literals['can_Perth_to_Inverness'] = \
            'you can go from Perth to Inverness'
        self.literals['can_Aberdeen_to_Inverness'] = \
            'you can go from Aberdeen to Inverness'
        self.literals['can_Aberdeen_to_Perth'] = \
            'you can go from Aberdeen to Perth'
        self.literals['can_Inverness_to_Aberdeen'] = \
            'you can go from Inverness to Aberdeen'
        self.literals['can_Inverness_to_Perth'] = \
            'you can go from Inverness to Perth'
        self.literals['can_Perth_to_Stirling'] = \
            'you can go from Perth to Stirling'
        self.literals['can_Perth_to_Kincardine'] = \
            'you can go from Perth to Kincardine'
        self.literals['can_Perth_to_Edinburgh'] = \
            'you can go from Perth to Edinburgh'
        self.literals['can_Kincardine_to_Edinburgh'] = \
            'you can go from Kincardine to Edinburgh'
        self.literals['can_Stirling_to_Edinburgh'] = \
            'you can go from Stirling to Edinburgh'

        self.literals['edinburgh_stirling_not_possible'] = \
            'you cannot go from Edinburgh to Stirling'
        self.literals['edinburgh_kincardine_not_possible'] = \
            'you cannot go from Edinburgh to Kincardine'
        self.literals['edinburgh_perth_not_possible'] = \
            'you cannot go from Edinburgh to Perth'
        self.literals['stirling_perth_not_possible'] = \
            'you cannot go from Stirling to Perth'
        self.literals['perth_aberdeen_not_possible'] = \
            'you cannot go from Perth to Aberdeen'
        self.literals['perth_inverness_not_possible'] = \
            'you cannot go from Inverness to Inverness'
        self.literals['aberdeen_inverness_not_possible'] = \
            'you cannot go from Aberdeen to Inverness'
        self.literals['aberdeen_perth_not_possible'] = \
            'you cannot go from Aberdeen to Perth'
        self.literals['inverness_aberdeen_not_possible'] = \
            'you cannot go from Inverness to Aberdeen'
        self.literals['inverness_perth_not_possible'] = \
            'you cannot go from Inverness to Perth'
        self.literals['perth_stirling_not_possible'] = \
            'you cannot go from Perth to Stirling'
        self.literals['perth_kincardine_not_possible'] = \
            'you cannot go from Perth to Kincardine'
        self.literals['perth_edinburgh_not_possible'] = \
            'you cannot go from Perth to Edinburgh'
        self.literals['kincardine_edinburgh_not_possible'] = \
            'you cannot go from Kincardine to Edinburgh'
        self.literals['stirling_edinburgh_not_possible'] = \
            'you cannot go from Stirling to Edinburgh'

        self.literals['Stirling1'] = 'go to Stirling'
        self.literals['Stirling2'] = 'go to Stirling'
        self.literals['Edinburgh1'] = 'go to Edinburgh'
        self.literals['Edinburgh2'] = 'go to Edinburgh'
        self.literals['Aberdeen1'] = 'go to Aberdeen'
        self.literals['Aberdeen2'] = 'go to Aberdeen'
        self.literals['Inverness1'] = 'go to Inverness'
        self.literals['Inverness2'] = 'go to Inverness'
        self.literals['Perth1'] = 'go to Perth'
        self.literals['Perth2'] = 'go to Perth'
        self.literals['Kincardine1'] = 'go to Kincardine'
        self.literals['Kincardine2'] = 'go to Kincardine'

        self.literals['system_malfunction'] = 'system malfunction'
        self.literals['require_immediate_landing'] = \
            'UAV requires immediate landing'
        self.literals['-ilsA'] = \
            'no Instrumental Landing System detected at airfield A'
        self.literals['-ilsB'] = \
            'no Instrumental Landing System detected at airfield B'
        self.literals['-vlpA'] = \
            'no visual landing at airfield A possible'
        self.literals['lvA'] = \
            'low visibility at airfield A'
        self.literals['-alpA'] = \
            'no automated landing possible at airfield A'

        self.literals['kick'] = 'a kick was detected'
        self.literals['need_speed'] = 'the well has to be shut quickly'
        self.literals['shallow_depth'] = 'the well is in a shallow depth'
        self.literals['do_kill'] = 'kill the kick'
        self.literals['HSP_very_low'] = 'HSP is very low'
        
# methods


    def process_nlg_doc(self, doc):
        summary = self.lexicalise(doc)
        print('--> After lex: %s' % repr(summary))
        summary = self.aggregate(summary, 3)
        print('--> After aggr: %s' % repr(summary))
#        summary = self.generate_re(summary, doc, Context(doc.ontology))
        summary = self.realise(summary)
        print('--> After realisation: %s' % repr(summary))
        summary = self.format(summary)
        print('--> After formatting: %s' % repr(summary))
        return summary

    def lexicalise(self, msgs):
        """ Lexicalise the given high-level structure using lexicalise
        from the lexicalisation package.
        
        """
        res = lexicalisation.lexicalise(msgs)
        return res

    def aggregate(self, msgs, limit):
        """ Run the messages through aggregation. """
        res = aggregation.aggregate(msgs, limit)
        return res

    def generate_re(self, msgs, context):
        """ Generate referring expressions. """
        # TODO: implement REG
        return msgs

    def realise(self, msgs):
        """ Perform linguistic realisation. """
        res = realisation.realise(msgs)
        return res

    def format(self, msgs, fmt='txt'):
        """ Convert the realised messages to given format. Text by default. """
        text = format.to_text(msgs)
        return text

    def document_to_text(self, doc):
        summary = self.lexicalise_doc(doc)
#        summary = aggregation.aggregate(summary)
#        summary = reg.generate(msgs, doc, Context(doc.ontology))
        summary = realisation.realise(summary)
        summary = format.to_text(summary)
        return summary

    def messages_to_text(self, messages):
        text = [str(x) for x in messages]
        text = map(lambda e: e[:1].upper() + e[1:], text)
        return ('.\n'.join(text))

    def lexicalise_doc(self, document):
        """ Create a list of syntax trees representing the sequence of actions
        in a given plan.
        
        """
        tasks = list(map(lambda x: self.lexicalise_task(x, document),
                            document.workflow.tasks()))
        return tasks

    def lexicalise_task(self, task, document):
        """ Convert a task to a syntax tree with lexical items in it. """
#        print('Lexicalising task %s' % str(task))
        params = task.input_params[:]
        key = task.name
        sent = self.templates.template(key)
        if None is sent:
            key = task.id
            sent = self.templates.template(key)
        if None != sent:
            self._replace_placeholders_with_params(sent, params)
        else:
            print('Key "%s" or id "%s" not found' % (task.name, task.id))
        return sent

    def task_to_text(self, task, document, context):
        """ Convert a task to text by lexicalising and performing REG. """
        msgs = [self.lexicalise_task(task, document)]
#        print('Before aggregation: %s' % msgs)
        msgs = self.synt_aggregation(msgs)
#        print('Before gre: %s' % msgs)
        msgs = self.gre(msgs, document, context)
#        print('Before text: %s' % msgs)
        if msgs == [None]: text = task.id
        else: text = self.messages_to_text(msgs)
        return text + '.'

    def _replace_placeholders_with_params(self, template, params):
#        print('Replacing params in template:\n%s' % str(template))
#        print('Params: \n\t %s' % str(params))
        for c in sentence_iterator(template):
            if (isinstance(c, PlaceHolder)):
                id = c.id
                var = params[id]
                c.object = var
#                print('Replacing parameter %d with %s' % (id, var))

    def gre(self, msgs, document, context):
        """ Replace placeholders with NPs
        The placeholders should already have names in them, so just replace
        each of them by an NP.
        
        """
        if context is None: context = Context(document.ontology)

        messages = deepcopy(msgs)
        for m in messages:
            self._replace_placeholders_with_nps(m, context)
        return messages

    def _replace_placeholders_with_nps(self, message, context):
        for i in sentence_iterator(message):
            if (not isinstance(i, PlaceHolder)):
                continue
            
            refexp = self.reg.gre(i.object, context)
#            np = NP(Word(refexp))
            # replace the placeholder by an RE
            replace_element(message, i, refexp)

    def synt_aggregation(self, messages, max=3):
        """ Take a list of messages and combine messages that are sufficiently
        similar.
        
        messages - a list of messages to combine
        max      - a maximum number of messages to aggregate
        
        The algorithm relies on shared structure of the messages. If, for 
        example, two messages share the subject, combine the VPs into 
        a conjunction. Do not combine more than 'max' messages into each other.

        """
        if messages is None: return
        if len(messages) < 2: return messages

        aggregated = list()
        i = 0
        while i < len(messages) - 1:
            msg, increment = self._do_aggregate(messages, i, max)
            aggregated.append(msg)
            i += increment

        return aggregated

    def _do_aggregate(self, messages, i, max):
        lhs = messages[i]
        j = i + 1
        increment = 1
        while j < len(messages) and self._can_aggregate(lhs, max):
            print('LHS = %s' % lhs)
            rhs = messages[j]
            if self._can_aggregate(rhs, max):
                tmp = try_to_aggregate(lhs, rhs)
                if tmp is not None:
                    lhs = tmp
                    increment += 1
                    j += 1
                else:
                    break
            # cannot aggregate. can we skip it?
            elif self._can_skip(messages, j):
                j += 1
                increment += 1
            else:
                break
        return (lhs, increment)

    def _can_aggregate(self, message, max):
        """ Return true if this message can be aggregated.
        max - maximum number of coordinates in a coordingated clause
        If the message does not have a coordinated clause or if the number 
        of coordinates is less then 'max', return True.

        """
        if message is None: return False
        for part in sentence_iterator(message):
            if not isinstance(part, CC):
                continue
            else:
                return (len(part.coords) < max)
        # simple sentence - no coordinated clause
        return True

    def _can_skip(self, messages, j):
        """ Return true if this element can be skipped. """
        return (messages[j] is None)


    def dialog_response_to_text(self, response):
        result = None
        try:
            message, parameter = response
            if 'justification' == message:
                text = self.realise_rule(parameter)
                text = text[0].upper() + text[1:]
                result = 'SYSTEM: ' + text + '.\n'
            else:
                text = self.realise_literal(parameter.consequent)
                text = text[0].upper() + text[1:]
                result = 'SYSTEM: ' + text
                reasoning = self.realise_antecedents(parameter.antecedent)
                if reasoning != '':
                    result += ' because ' + reasoning
                result += '.\n'
        except Exception as e:
            print('Exception %s' % str(e))
            print('response: %s' % str(response))
            result = str(response)

        return result

    # TODO: add vulnerabilities to defeasible rules when they undercut the rule
    def realise_rule(self, rule):
        result = self.realise_literal(rule.consequent)
        if len(rule.antecedent) > 0:
            result += ' because '
            result += self.realise_antecedents(rule.antecedent)
        return result

    def realise_literal(self, lit):
        if str(lit) in self.literals:
            return self.literals[str(lit)]
        else:
            print('%s not in literals' % lit)
            return str(lit)

    def realise_antecedents(self, antecedent):
        result = ''
        if antecedent == []: return result
        reasons = [self.realise_literal(x) for x in antecedent]
        print(reasons)
        if len(reasons) >=2:
            last_two = reasons[-2:]
            result += ', '.join(reasons[2:])
            result += last_two[0] + ' and ' + last_two[1]
        else:
            result += reasons[0]
        return result

#self.responses['justify'] = ''
#self.responses['argument_against_label_IN'] = ''
#self.responses['argument_against_label_OUT'] = ''
#self.responses['argument_against_label_UNDEC'] = ''





