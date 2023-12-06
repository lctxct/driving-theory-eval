import curses
import textwrap

from curses.textpad import rectangle
from random import shuffle

IMAGE_SUPPORT = False

#TODO: look at xtermjs 
#TODO: add image support (hard)
#TODO: add review section

class Question:
    def __init__(self, qn: str, ans: list[str], img=None):
        self.qn_width = 77
        self.ans_width = 89

        self.qn = self.prep_qn(qn)
        self.ans = self.prep_ans(ans)
        self.img = self.prep_img(img)

        self.marked = -1

    def prep_qn(self, qn):
        return textwrap.fill(qn, width=self.qn_width)

    def prep_ans(self, ans):
        ans_final = []
        for i, a in enumerate(ans):
            correct = True if "[x]" in a else False
            assert "] " in a, "something's wrong " + repr(ans)
            tmp = textwrap.fill(a[a.index("] ")+2:], width=self.ans_width)

            ans_final.append((correct, tmp))
        
        shuffle(ans_final)
        return ans_final
    
    def prep_img(self, image):
        #TODO: ascii art?
        # try https://pypi.org/project/ascii-magic/
        return None

class App:
    def __init__(self, stdscr):
        self.stdscr = stdscr

class Menu(App):
    def __init__(self, stdscr):
        App.__init__(self, stdscr)
        self.page = 0

        # page0 settings (btt/ftt)
        self.stages = ["btt", "ftt"]
        self.stage_select = 1  # ftt by default / btt
        self.stage_hover = 1

        # page 1 settings (booklet / random / all)
        self.booklets = ["All (500)", "Random (50)", 
                         "Booklet 1", "Booklet 2", "Booklet 3", "Booklet 4", "Booklet 5", 
                         "Booklet 6", "Booklet 7", "Booklet 8", "Booklet 9", "Booklet 10"]

        self.test_select = -1
        self.test_hover = 0
    
    def draw_all(self):
        self.stdscr.clear()
        if self.page == 0:
            self.__draw_page0()
        elif self.page == 1:
            self.__draw_page1()
        self.stdscr.refresh()

    def process_key(self, key):
        if self.page == 0:
            self.__key_page0(key)
        elif self.page == 1:
            self.__key_page1(key)
        
        if self.page == 2:
            self.page = 0
            return 1
        
        return 0

    def __draw_page0(self):
        btt_op = "[x]" if self.stage_select == 0 else "[ ]"
        ftt_op = "[x]" if self.stage_select == 1 else "[ ]"

        btt_col = not self.stage_hover
        ftt_col = self.stage_hover

        self.stdscr.addstr(10, 50, "SELECT TEST")
        self.stdscr.addstr(12, 52, btt_op + " BTT", curses.color_pair(btt_col))
        self.stdscr.addstr(13, 52, ftt_op + " FTT", curses.color_pair(ftt_col))

    def __key_page0(self, key):
        if key == curses.KEY_UP and self.stage_hover > 0:
            self.stage_hover -= 1
        elif key == curses.KEY_DOWN and self.stage_hover < 1:
            self.stage_hover += 1
        elif key == curses.KEY_RIGHT:
            self.page += 1
        elif key == 32:  # spacebar 
            self.stage_select = self.stage_hover if self.stage_hover != self.stage_select else -1

    def __draw_page1(self):
        self.stdscr.addstr(5, 50, "SELECT BOOKLET")

        for i, book in enumerate(self.booklets): 
            is_highlighted = (i == self.test_hover)
            is_selected = (i == self.test_select)

            op = "[x]" if is_selected else "[ ]"
            col = 1 if is_highlighted else 0

            self.stdscr.addstr(6+i, 50, f"{op} {book.upper()}", curses.color_pair(col))

    def __key_page1(self, key):
        if key == curses.KEY_UP:
            self.test_hover = (self.test_hover - 1) % len(self.booklets)
        elif key == curses.KEY_DOWN:
            self.test_hover = (self.test_hover + 1) % len(self.booklets)
        elif key == curses.KEY_RIGHT:
            # check have not selected option 
            self.page += 1
        elif key == curses.KEY_LEFT:
            self.page -= 1
        elif key == 32:  # spacebar 
            self.test_select = self.test_hover if self.test_hover != self.test_select else -1

    def check_complete(self):
        # TODO: would be better if warn when incomplete instead 
        if self.stage_select == -1:
            # default to ftt 
            self.stage_select = 1
        
        if self.test_select == -1:
            # default to ALL 
            self.test_select = len(self.booklets) - 1

        return self.stage_select != -1 and self.test_select != -1
        
    def load_questions(self):
        self.check_complete()

        qns = []
        name = f"{self.stages[self.stage_select]} {self.booklets[self.test_select]}".upper()
    
        lines = []  
        match self.test_select:
            case 0:  # all
                for i in range(1, 11):
                    filename = f"booklets/ftt/booklet{i}.txt"
                    lines += [line.strip() for line in open(filename)]
            case 1:  # shuffle
                for i in range(1, 11):
                    filename = f"booklets/ftt/booklet{i}.txt"
                    lines += [line.strip() for line in open(filename)]
            case _:  # 2-
                filename = f"booklets/ftt/booklet{self.test_select-1}.txt"
                lines = [line.strip() for line in open(filename)]
                
        for i in range(0, len(lines), 6):
            # Expected format:
            #1 <question>
            #2 [ ] <ans1>
            #3 [x] <ans2>  <-- right option
            #4 [ ] <ans3>
            #5 <imagepath>  
            #6 <blankline>
            q = lines[i]
            ans = [lines[i+1], lines[i+2], lines[i+3]]
            img = None

            if IMAGE_SUPPORT:
                img = lines[i+4]
            
            qns.append(Question(q, ans, img))

        match self.test_select:
            case 0:  # all 
                shuffle(qns)
            case 1:
                shuffle(qns)
                qns = qns[:50]
        
        return name, qns

class Test(App):
    def __init__(self, stdscr, qns, label):
        App.__init__(self, stdscr)
        self.label = label
        self.loaded_qns = qns

        self.score = 0 
        self.qn_idx = 0 
        self.wrong_qns = []

        self.cur_rect = 0
        self.marked_rect = -1  # by default, no rect selected
        self.just_marked = False
    
    def draw_all(self):
        cur_qn = self.loaded_qns[self.qn_idx]

        self.stdscr.clear()
        self.__draw_header()
        self.__draw_question(cur_qn.qn)
        self.__draw_image()
        self.__draw_rectangles(cur_qn.ans)
        self.stdscr.refresh()

    def process_key(self, key):
        cur_qn = self.loaded_qns[self.qn_idx]

        self.just_marked = False 

        if key == curses.KEY_UP and self.cur_rect > 0:
            self.cur_rect -= 1
        elif key == curses.KEY_DOWN and self.cur_rect < 2:
            self.cur_rect += 1
        elif key == curses.KEY_LEFT and self.qn_idx > 0:
            self.qn_idx -= 1
            self.cur_rect = 0
            self.marked_rect = self.loaded_qns[self.qn_idx].marked
        elif key == curses.KEY_RIGHT and self.qn_idx < len(self.loaded_qns) - 1:
            self.qn_idx += 1
            self.cur_rect = 0
            self.marked_rect = self.loaded_qns[self.qn_idx].marked
        elif key == curses.KEY_RIGHT:  # get results
            return 2
        elif key == 32:  # spacebar 
            # if current rectangle already selected 
            if self.marked_rect == self.cur_rect:
                # unselect rectangle
                self.marked_rect = -1 
            else:
                # if current rectangle not selected
                self.marked_rect = self.cur_rect
                self.just_marked = True
                # if answering question for first time
                if cur_qn.marked == -1:
                    if cur_qn.ans[self.marked_rect][0]:  # if correct
                        self.score += 1
                    else:
                        self.wrong_qns.append(cur_qn)

                cur_qn.marked = self.marked_rect
        elif key == 113: # q 
            return 0
        
        return 1

    def __draw_header(self):
        score = f"SCORE: {self.score} / {len(self.loaded_qns)}"

        self.stdscr.addstr(0, 2, f"QUESTION: {self.qn_idx+1} / {len(self.loaded_qns)}")
        self.stdscr.addstr(0, 51-len(self.label)//2, self.label)
        self.stdscr.addstr(0, 101-len(score), score)

    def __draw_question(self, qn):
        space = 1
        height = 6
        width = 80

        r = (space, space, height+space, width+space)

        # draw
        rectangle(self.stdscr, *r)
        for i, q in enumerate(qn.split("\n")):
            self.stdscr.addstr(r[0]+1+i, r[1]+2, q)

    def __draw_image(self):
        space = 1
        offset_width = 81
        height = 6
        width = 19

        r = (space, space+offset_width, height+space, width+space+offset_width)

        # draw
        rectangle(self.stdscr, *r)
        self.stdscr.addstr(r[0]+1+1, r[1]+4, "<image not")
        self.stdscr.addstr(r[0]+1+2, r[1]+4, " supported")
        self.stdscr.addstr(r[0]+1+3, r[1]+4, "    (yet)>")

    def __draw_rectangles(self, ans):
        #TODO: too hardcoded
        offset_height = 7
        height = 4
        width = 92
        space = 1

        rects = [[i+space+i*height+offset_height for i in range(3)],  # top y
                        [space for _ in range(3)],  # top x
                        [i+space+(i+1)*height+offset_height for i in range(3)], 
                        [space+width for _ in range(3)]]

        rects = list(zip(*rects))

        offset_width = width 
        height = 4
        width = 8
        space = 1

        mcq_rects = [[i+space+i*height+offset_height for i in range(3)],  # top y
                            [offset_width+space for _ in range(3)],  # top x
                            [i+space+(i+1)*height+offset_height for i in range(3)], 
                            [offset_width+space+width for _ in range(3)]]
        
        mcq_rects = list(zip(*mcq_rects))

        for i, r in enumerate(rects):
            is_highlighted = (i == self.cur_rect)
            is_marked = (i == self.marked_rect)
            is_correct = (is_marked and ans[i][0])

            # start drawing
            color_idx = 0
        
            if is_highlighted:
                if not self.just_marked: 
                    color_idx = 1
                elif is_correct:
                    color_idx = 2
                else:  # wrong 
                    color_idx = 3
            elif is_marked:
                if is_correct:
                    color_idx = 2
                else:  # wrong
                    color_idx = 3
            else:
                color_idx = 0
                
            self.stdscr.attron(curses.color_pair(color_idx))
            # add answer rectangle 
            rectangle(self.stdscr, *r)
            
            # add answer text 
            offset = ans[i][1].count("\n")
            if offset:
                for line, a in enumerate(ans[i][1].split("\n")):
                    self.stdscr.addstr(r[0]+1+line, r[1]+2, a)
            else:
                self.stdscr.addstr(r[0]+2, r[1]+2, ans[i][1])
            
            # add marker rectangle
            rectangle(self.stdscr, *mcq_rects[i])
            if is_marked: 
                self.stdscr.addstr(mcq_rects[i][0]+2, mcq_rects[i][1]+4, "X")
            self.stdscr.attroff(curses.color_pair(color_idx))
    
    def get_result(self):
        return self.score, len(self.loaded_qns)

class Result(App):
    def __init__(self, stdscr, score, total):
        App.__init__(self, stdscr)
        self.score = score
        self.total = total
    
    def draw_all(self):
        self.stdscr.clear()
        self.__draw_result()
        self.stdscr.refresh()

    def __draw_result(self):
        ratio = round(self.score / self.total, 5)

        height, width = self.stdscr.getmaxyx()
        msg1 = f"YOU SCORED {self.score}/{self.total}"
        msg2 = f"WHICH IS {ratio*100}%"


        self.stdscr.addstr(height//2-1, (width-len(msg1))//2, msg1)
        self.stdscr.addstr(height//2, (width-len(msg2))//2, msg2)
        if ratio >= 0.9:
            self.stdscr.addstr(height//2+1, (width-4)//2, "PASS", curses.color_pair(2))
        else:
            self.stdscr.addstr(height//2+1, (width-4)//2, "FAIL", curses.color_pair(3))
    
    def process_key(self, key):
        if key == 113: # q 
            return 0
        
        return 2

def main(stdscr):
    curses.curs_set(0)  # hide cursor
    curses.start_color()
    # selection color 
    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    # correct color 
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    # wrong color 
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)

    state = 0 

    # settings
    menu = Menu(stdscr)
    # test
    test = None
    # result
    result = None

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        if height < 3 or width < 30:
            break 

        if height < 23 or width < 103:
            # Display warning message if screen size is too small
            warn1 = f"WARNING: ({height}, {width}) IS TOO SMALL"
            warn2 = "PLEASE RESIZE TO (23, 103)"
            stdscr.addstr(height // 2, (width - len(warn1)) // 2, warn1, curses.color_pair(1))
            stdscr.addstr(height // 2+1, (width - len(warn2)) // 2, warn2, curses.color_pair(1))
            stdscr.refresh()
            key = stdscr.getch()  # Wait for user input
            if key == 27:  # esc
                break
            continue

        # draw display
        match state:
            case 0:
                menu.draw_all() 
            case 1:
                test.draw_all()
            case 2: 
                result.draw_all()

        key = stdscr.getch()
        if key == 27:  # esc
            break

        # process key 
        match state:
            case 0:
                state = menu.process_key(key)
                if state == 1:
                    name, qns = menu.load_questions()
                    test = Test(stdscr, qns, name)
            case 1: 
                state = test.process_key(key)
                if state == 2:
                    score, total = test.get_result()
                    result = Result(stdscr, score, total)
            case 2: 
                state = result.process_key(key)
                if state == 0:
                    menu = Menu(stdscr)

if __name__ == "__main__":
    curses.wrapper(main)
