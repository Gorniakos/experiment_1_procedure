from psychopy import visual, event, core, gui, logging
from psychopy.hardware import keyboard
from typing import Dict
from os.path import join

import random
import yaml
import csv
import codecs
import pandas as pd
import numpy as np

def main():
    #Loading config file
    conf: Dict = yaml.load(open('config.yaml', encoding='utf-8'), Loader=yaml.SafeLoader)

    win = visual.Window(size = (conf['SCREEN_RESOLUTION']))

    #Getting time of study start
    General_clock = core.Clock(format = str)
    print('Study time: ' + str(General_clock.getTime()))
    study_time = General_clock.getTime()

    #Providing participants info
    info: Dict = {'ID': ''}
    dict_dlg = gui.DlgFromDict(dictionary=info, title='Provide participant info')
    if not dict_dlg.OK:
        abort_with_error('Info dialog terminated.')

    #Checking whether ID is integer
    valid_input = False
    while not valid_input:
        try:
            part_int = int(info['ID'])
            valid_input = True
        except ValueError:
            dlg = gui.Dlg(title='Input Error')
            dlg.addText('Please enter a valid integer for ID.')
            dlg.show()
            if not dlg.OK:
                core.quit()  # User pressed cancel
            dict_dlg = gui.DlgFromDict(dictionary=info, title='Provide participant info')
            if not dict_dlg.OK:
                core.quit()  # User pressed cancel

    PART_ID = info['ID']
    logging.LogFile(join('results', f'{PART_ID}.log'), level=logging.INFO)  # errors logging

    #Counterbalancing response keys based on participants ID
    if part_int % 2 == 0:
        animal_key = conf['REACTION_KEYS'][0]
        item_key = conf['REACTION_KEYS'][1]
    else:
        animal_key = conf['REACTION_KEYS'][1]
        item_key = conf['REACTION_KEYS'][0]

    clock = core.Clock()

    RESULTS = []
    RESULTS.append(['PART_ID', 'Study time', 'Block_number', 'Trial_number', 'Correct_key', 'Key_pressed', 'Reaction_time', "Stim_name", 'Context', 'Target', 'Target_type', 'Accuracy'])

    block_no = 1
    trial_no = 1

    #Saving results to csv file
    def save_results():
        file_name = PART_ID + ".csv"
        with open(join('results', file_name), 'w', encoding='utf-8') as beh_file:
            beh_writer = csv.writer(beh_file)
            beh_writer.writerows(RESULTS)
        logging.flush()

    #Loading messages (instructions etc.) from txt files
    def read_text_from_file(file_name: str, insert: str = '') -> str:
        if not isinstance(file_name, str):
            logging.error('Problem with file reading, filename must be a string')
            raise TypeError('file_name must be a string')
        msg = list()
        with codecs.open(file_name, encoding='utf-8', mode='r') as data_file:
            for line in data_file:
                if not line.startswith('#'):  # if not commented line
                    if line.startswith('<--insert-->'):
                        if insert:
                            msg.append(insert)
                    else:
                        msg.append(line)
        return ''.join(msg)

    #Showing info loaded with read_text_from_file function
    def show_info(win: visual.Window, file_name: str, insert: str = '') -> None:
        msg = read_text_from_file(file_name, insert=insert)
        msg = visual.TextStim(win, color='white', text=msg)
        msg.draw()
        win.flip()
        key = event.waitKeys(keyList=['f7', 'return', 'space', 'left', 'right'])
        if key == ['f7']:
            abort_with_error('Experiment finished by user on info screen! F7 pressed.')
        win.flip()


    #Creating list of stimuli based on provided csv file and prepare dictionary with properties of each stimuli aassigned to stimuli's name as a key 
    def prepare_stim_list():
        stim_list = []
        stim_dict_prop = {}
        
        with open('stim_list.csv', mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
                    
            for row in reader:
                print(row)
                cleaned_row = [cell.replace(";", "") for cell in row]
                stim_name = cleaned_row[0]
                background = cleaned_row[1] 
                target = cleaned_row[2] 
                object_type = cleaned_row[3] 
                
                stim_list.append(stim_name)
                stim_properties = [background, target, object_type]
                stim_dict_prop[stim_name] = stim_properties
            
            del stim_list[0]
            del stim_dict_prop['\ufeffname']
                        
        return stim_dict_prop, stim_list

    #Running signle trial
    def run_trial(clock, stim, stim_dict_prop):
        mask = visual.rect.Rect(win, width = 0.3, height = 0.45, fillColor = 'grey', pos = (0.3, -0.2))
        fixation = visual.TextStim(win, text = "+", color = 'white')
        fixation_target = visual.TextStim(win, text = "+", color = 'white', pos = (0.3, -0.2))
        
        if animal_key == 'a':
            clue_text = 'Zwierzę: A                       Przedmiot: L'
        else:
            clue_text = 'Przedmiot: A                       Zwierzę: L'
            
        response_clue = visual.TextStim(win, text = clue_text, color = 'white', pos = (0,-0.8))
        
        stim_image = visual.ImageStim(win, image = f'stimuli/{stim}')
        
        correct_key = None
        
        stim_name = str(stim)    
        background = stim_dict_prop[stim_name][0]
        target = stim_dict_prop[stim_name][1]
        target_type = stim_dict_prop[stim_name][2]
        
        if target_type == 'animal':
                correct_key = animal_key
        else:
            correct_key = item_key
        
        #Empty screen before each trial
        for _ in range(conf['EMPTY_SCREEN_TIME']):
            response_clue.draw()
            win.flip()

        #Fixation
        for _ in range(conf['FIXATION_TIME']):
            fixation.draw()
            response_clue.draw()
            win.flip()        

        #Presenting context with masked taget
        for _ in range(conf['MASKED_PRESENTATION_TIME']):
            stim_image.draw()
            mask.draw()
            response_clue.draw()
            win.flip()
                
        #Fixation on target        
        for _ in range(conf['TARGET_FIXATION_TIME']):
            stim_image.draw()
            mask.draw()
            response_clue.draw()
            fixation_target.draw()
            win.flip()
        
        event.clearEvents()
        win.callOnFlip(clock.reset)
        
        #Full stimuli
        for _ in range(conf['FULL_STIM_TIME']):
            reaction = event.getKeys(keyList = conf['REACTION_KEYS'])
            rt = clock.getTime()
            if reaction:
                break
            stim_image.draw()
            response_clue.draw()
            win.flip()
            
        if reaction:
            response_key = reaction[0]
            reaction_time = rt
            if response_key == correct_key:
                accuracy = 1
            else:
                accuracy = 0
            
        else:
            response_key = 'No response'
            reaction_time = -1
            accuracy = -1
        
        return correct_key, response_key, reaction_time, stim_name, background, target, target_type, accuracy

    #Procedure
    show_info(win, 'messages/Instruction_1.txt')
    show_info(win, 'messages/Instruction_2.txt')
    stim_dict_prop, stim_list = prepare_stim_list()
    for block in range(conf['NO_BLOCKS']):
        random.shuffle(stim_list)
        trial_no = 1 # to start trial count for each block separately
        for stim in stim_list:
            correct_key, response_key, reaction_time, stim_name, background, target, target_type, accuracy = run_trial(clock, stim, stim_dict_prop)
            RESULTS.append([PART_ID, study_time, block_no, trial_no, correct_key, response_key, reaction_time, stim_name, background, target, target_type, accuracy])
            trial_no += 1
        if block_no != (conf['NO_BLOCKS']):
            show_info(win, 'messages/Break.txt')
        block_no += 1
    save_results()
    show_info(win, 'messages/End.txt')

if __name__ == '__main__':
    main()