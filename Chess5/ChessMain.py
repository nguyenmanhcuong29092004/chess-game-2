"""
Main driver file.
Handling user input.
Displaying current GameStatus object.
"""
import pygame as p
import ChessEngine, ChessAI
import sys
from multiprocessing import Process, Queue

BOARD_WIDTH = BOARD_HEIGHT = 550#Kích thước của của bàn cờ
MOVE_LOG_PANEL_WIDTH = 250#Hiển thị kích thước của bảng lịch sử di chuyển
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8#số ô cho mỗi hàng, mỗi mỗi cột
SQUARE_SIZE = BOARD_HEIGHT // DIMENSION#kích thước mỗi ô
MAX_FPS = 15#số khung hình tối đa
IMAGES = {}#Lưu trữ hình ảnh


def loadImages():
    """
    Initialize a global directory of images.
    This will be called exactly once in the main.
    """
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']

    #Tải ảnh xuống
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"), (SQUARE_SIZE, SQUARE_SIZE))


def main():
    """
    The main driver for our code.
    This will handle user input and updating the graphics.
    """
    p.init()#Khởi tạo thư viện
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))#Tạo cửa sổ với kích thước thiết lập
    clock = p.time.Clock()#kiểm soát tốc độ trò chơi
    screen.fill(p.Color("white"))#Đổ màu trắng lên toàn bộ của sổ
    p.display.set_caption("CHESS GAME")#Tên trò chơi
    game_state = ChessEngine.GameState()#Khởi tạo đối tượng game state
    valid_moves = game_state.getValidMoves()#danh sách nước đi hợp lệ
    move_made = False  # theo dõi nước đi thực hiện chưa
    animate = False  #xác định xem nước đi được thực hiện chưa
    loadImages()#Tải ảnh  
    running = True#Theo dõi trò chơi có chạy ko
    square_selected = ()  #Lưu trữ tuple(hàng, cột) theo dõi ô cuối cùng người chơi đi
    player_clicks = []  #Theo dõi những lần người chơi nhấn chuột, lưu dưới dạng tuple(hàng,cột)
    game_over = False#Xác định xem trò chơi kết thúc chưa
    ai_thinking = False#xác định xem máy tính có đang suy nghĩ về nước đi ko
    move_undone = False#xác định nước đi có undo ko
    move_finder_process = None#ban đầu, ko có tiến trình tìm nước đi của máy tính
    move_log_font = p.font.SysFont("Arial", 18, False, False)#khởi tạo 1 font chữ để hiện thị thông tin lịch sử nước đi
    player_one = True  # xác định quân cờ người chơi có là trắng ko
    player_two = False  

    while running:
        human_turn = (game_state.white_to_move and player_one) or (not game_state.white_to_move and player_two)#xác định lượt đi của người chơi

        #vòng lặp xử lí tất cả các sự kiện
        for e in p.event.get():
            if e.type == p.QUIT:#nếu event là quit
                p.quit()
                sys.exit()
            # nếu event là nhấn chuột
            elif e.type == p.MOUSEBUTTONDOWN:
                if not game_over:
                    location = p.mouse.get_pos()#lấy vị trí hiện tại con chuột
                    col = location[0] // SQUARE_SIZE
                    row = location[1] // SQUARE_SIZE 
                    if square_selected == (row, col) or col >= 8:  #kiểm tra xem người chơi có ấn vào ô để hủy hay nhấn vào ô nằm ngoài bàn cờ ko
                        square_selected = () # hủy chọn ô
                        player_clicks = []  # xóa danh sách lưu trữ nhấn chuột
                    else:
                        square_selected = (row, col)
                        player_clicks.append(square_selected)  
                    if len(player_clicks) == 2 and human_turn:  # kiểm tra người chơi nhân chuột đủ 2 lần và đến lượt của họ
                        move = ChessEngine.Move(player_clicks[0], player_clicks[1], game_state.board)#di chuyển từ nước đầu tới nước đích
                        #lặp qua ds nước đi hợp lệ
                        for i in range(len(valid_moves)):
                            if move == valid_moves[i]:#nếu hợp lệ
                                game_state.makeMove(valid_moves[i])#thực thực hiện nước đi
                                move_made = True#đánh dấu nước đi dc thực hiện
                                animate = True#Đánh dấu cần thực hiện hiệu ứng di chuyển
                                square_selected = ()  
                                player_clicks = []
                        if not move_made:#nếu ko có nước đi thực hiện do nước đi không hợp lệ
                            player_clicks = [square_selected]#chỉ lưu trữ lần nhấn chuột hiện tại

            # nếu event là bàn phím
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:  # hoàn tác nước đi nếu nhấn z
                    game_state.undoMove()
                    move_made = True
                    animate = False
                    game_over = False
                    if ai_thinking:#nếu máy tính đang suy nghĩ thì hủy tiến trình đó
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = True
                if e.key == p.K_r:  # thiết lập lại game nếu nhấn r
                    game_state = ChessEngine.GameState()
                    valid_moves = game_state.getValidMoves()
                    square_selected = ()
                    player_clicks = []
                    move_made = False
                    animate = False
                    game_over = False
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = True

        # AI tìm kiếm nước đi
        if not game_over and not human_turn and not move_undone:#nếu game ko kết thúc và đến lượt của AI
            if not ai_thinking:
                ai_thinking = True
                return_queue = Queue()  # lưu tiến trình nước đi
                move_finder_process = Process(target=ChessAI.findBestMove, args=(game_state, valid_moves, return_queue))# tạo 1 tiến trình tốt nhất để tìm nước đi tốt nhất cho máy tính
                move_finder_process.start()

            if not move_finder_process.is_alive():#kiểm tra xem tiến trình kết thúc chưa
                ai_move = return_queue.get()#lấy nước đi
                if ai_move is None:#nếu ko có nước đi tốt thì lấy ngẫu nhiên
                    ai_move = ChessAI.findRandomMove(valid_moves)
                game_state.makeMove(ai_move)#thực hiện nước đi
                move_made = True
                animate = True
                ai_thinking = False

        #kiểm tra xem có nước đi được thực hiện và thực hiện hiệu ứng di chuyển
        if move_made:
            if animate:#thực hiện hiệu ứng di chuyển
                animateMove(game_state.move_log[-1], screen, game_state.board, clock)
            valid_moves = game_state.getValidMoves()#cập nhật ds nc đi hợp lệ mới
            move_made = False
            animate = False
            move_undone = False

        drawGameState(screen, game_state, valid_moves, square_selected)#vẽ bàn cờ

        #nếu game ko kết thúc thì vẽ lịch sử nước đi lên màn hình
        if not game_over:
            drawMoveLog(screen, game_state, move_log_font)

        #kiểm tra chiếu tướng
        if game_state.checkmate:
            game_over = True
            if game_state.white_to_move:#đen thắng
                drawEndGameText(screen, "Black wins by checkmate")
            else:#trắng thắng
                drawEndGameText(screen, "White wins by checkmate")
        
        #kiểm tra do bị bế tắc(hòa cờ)
        elif game_state.stalemate:
            game_over = True
            drawEndGameText(screen, "Stalemate")

        clock.tick(MAX_FPS)#điều chỉnh tốc độ khung hình
        p.display.flip()#cập nhật thay đổi

#Vex bàn cờ hiện tại
def drawGameState(screen, game_state, valid_moves, square_selected):
    drawBoard(screen)  #vẽ ô vuông
    highlightSquares(screen, game_state, valid_moves, square_selected)#vẽ màu cho các nước đi 
    drawPieces(screen, game_state.board)  # vẽ quân cờ

#vẽ các ô vuông trên bàn cờ
def drawBoard(screen):
    global colors#lưu trữ màu ô cờ
    colors = [p.Color("white"), p.Color("plum")]
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            color = colors[((row + column) % 2)]#xác định màu cho ô
            p.draw.rect(screen, color, p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))#vẽ ô cờ


#vẽ màu cho các nước đi 1 quân cờ có thể đi đến
def highlightSquares(screen, game_state, valid_moves, square_selected):
    """
    Highlight square selected and moves for piece selected.
    """
    if (len(game_state.move_log)) > 0:#Kiểm tra xem đã có ít nhất một nước đi trong lịch sử nước đi (move_log) của trò chơi hay chưa.
        last_move = game_state.move_log[-1]#lấy nước đi cuối cùng và tô màu green cho ô
        s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
        s.set_alpha(100)
        s.fill(p.Color('green'))
        screen.blit(s, (last_move.end_col * SQUARE_SIZE, last_move.end_row * SQUARE_SIZE))
    
    
    if square_selected != ():#kiểm tra xem có ô nào đang dc chọn ko
        row, col = square_selected#lấy tọa đô
        if game_state.board[row][col][0] == (
                'w' if game_state.white_to_move else 'b'):  #Kiểm tra xem ô đang chọn có khớp màu quân người chơi ko
            # Tô màu cho ô đang chọn
            s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
            s.set_alpha(100)  
            s.fill(p.Color('blue'))
            screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
            # Tô màu cho đường đi của quân
            s.fill(p.Color('yellow'))
            for move in valid_moves:
                if move.start_row == row and move.start_col == col:
                    screen.blit(s, (move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE))

#vẽ quân cờ
def drawPieces(screen, board):
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            piece = board[row][column]
            if piece != "--":#nếu ô không trống
                screen.blit(IMAGES[piece], p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


#vẽ bảng ghi chép các nước đi trong trò chơi cờ vua
def drawMoveLog(screen, game_state, font):
    move_log_rect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)#tạo bảng
    p.draw.rect(screen, p.Color('black'), move_log_rect)#vẽ bảng màu đen
    move_log = game_state.move_log#lấy danh sách cac nước đi
    move_texts = []#Tạo ds lưu trữ văn bản các nước đi

    # tạo ra một danh sách move_texts để biểu diễn các nước đi trong trò chơi cờ vua dưới dạng văn bản để hiển thị trong bảng ghi chép.
    for i in range(0, len(move_log), 2):
        move_string = str(i // 2 + 1) + '. ' + str(move_log[i]) + " "
        if i + 1 < len(move_log):
            move_string += str(move_log[i + 1]) + "     "
        move_texts.append(move_string)

    moves_per_row = 3
    padding = 5
    line_spacing = 2
    text_y = padding
    for i in range(0, len(move_texts), moves_per_row):
        text = ""
        for j in range(moves_per_row):
            if i + j < len(move_texts):
                text += move_texts[i + j]

        text_object = font.render(text, True, p.Color('white'))
        text_location = move_log_rect.move(padding, text_y)
        screen.blit(text_object, text_location)
        text_y += text_object.get_height() + line_spacing

#Hiển thị thông báo kết thúc
def drawEndGameText(screen, text):
    font = p.font.SysFont("Helvetica", 32, True, False)#font
    text_object = font.render(text, False, p.Color("gray"))#chứa dòng chữ
    text_location = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - text_object.get_width() / 2,
                                                                 BOARD_HEIGHT / 2 - text_object.get_height() / 2)#vị trí
    screen.blit(text_object, text_location)#vẽ
    text_object = font.render(text, False, p.Color('black'))#tạo hiệu ứng đổ bóng
    screen.blit(text_object, text_location.move(2, 2))

#Tạo hiệu ứng từ nước đâu đến nước kết thúc
def animateMove(move, screen, board, clock):
    global colors
    #tính toán sự thay đổi vị trí
    d_row = move.end_row - move.start_row
    d_col = move.end_col - move.start_col
    #số lượng khung hình (frames) 
    frames_per_square = 10  #cho 1 nước
    frame_count = (abs(d_row) + abs(d_col)) * frames_per_square

    #vòng lặp duyệt qua từng khung hình
    for frame in range(frame_count + 1):
        row, col = (move.start_row + d_row * frame / frame_count, move.start_col + d_col * frame / frame_count)
        drawBoard(screen)
        drawPieces(screen, board)
        # xóa quân cờ ở ô đích
        color = colors[(move.end_row + move.end_col) % 2]
        end_square = p.Rect(move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        p.draw.rect(screen, color, end_square)
        # vẽ quân đã ăn
        if move.piece_captured != '--':
            if move.is_enpassant_move:
                enpassant_row = move.end_row + 1 if move.piece_captured[0] == 'b' else move.end_row - 1
                end_square = p.Rect(move.end_col * SQUARE_SIZE, enpassant_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            screen.blit(IMAGES[move.piece_captured], end_square)
        # vẽ nước di chuyển
        screen.blit(IMAGES[move.piece_moved], p.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        p.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()