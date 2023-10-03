"""
Storing all the information about the current state of chess game.
Determining valid moves at current state.
It will keep move log.
"""


class GameState:
    def __init__(self):
        """
        Board is an 8x8 2d list, each element in list has 2 characters.
        The first character represents the color of the piece: 'b' or 'w'.
        The second character represents the type of the piece: 'R', 'N', 'B', 'Q', 'K' or 'p'.
        "--" represents an empty space with no piece.
        """
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]]
        self.moveFunctions = {"p": self.getPawnMoves, "R": self.getRookMoves, "N": self.getKnightMoves,
                              "B": self.getBishopMoves, "Q": self.getQueenMoves, "K": self.getKingMoves}
        self.white_to_move = True
        self.move_log = []#danh sách nước đi
        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)
        self.checkmate = False
        self.stalemate = False
        self.in_check = False#cho biết 1 bên có đang bị chiếu ko
        self.pins = []#danh sách các quan cờ bị chặn bởi quân cờ khác
        self.checks = []#danh sách các quân cờ đang chiếu vua
        self.enpassant_possible = ()  # xác định nước đi enpassant cho quân tốt
        self.enpassant_possible_log = [self.enpassant_possible]
        self.current_castling_rights = CastleRights(True, True, True, True)#quyền đổi xe và vua
        self.castle_rights_log = [CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                               self.current_castling_rights.wqs, self.current_castling_rights.bqs)]

    def makeMove(self, move):
        """
        Takes a Move as a parameter and executes it.
        (this will not work for castling, pawn promotion and en-passant)
        """
        #xóa quân cờ vị trí ban đầu và cập nhật vào vị trí đích
        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.move_log.append(move)  
        self.white_to_move = not self.white_to_move  

        # cập nhật vị trí của quân vua để theo dõi chiếu tướng
        if move.piece_moved == "wK":
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_moved == "bK":
            self.black_king_location = (move.end_row, move.end_col)

        # xử lí trường hợp khi quân tốt xuống cuối bàn cờ
        if move.is_pawn_promotion:
            # if not is_AI:
            #    promoted_piece = input("Promote to Q, R, B, or N:") #take this to UI later
            #    self.board[move.end_row][move.end_col] = move.piece_moved[0] + promoted_piece
            # else:
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + "Q"

        # Nước đi enpassant
        if move.is_enpassant_move:
            self.board[move.start_row][move.end_col] = "--"  # capturing the pawn

        # Kiểm tra xem nước đi enpassant có thực hiện được hay không
        if move.piece_moved[1] == "p" and abs(move.start_row - move.end_row) == 2:  # only on 2 square pawn advance
            self.enpassant_possible = ((move.start_row + move.end_row) // 2, move.start_col)#cập nhật vị trí enpassant nếu dk t/m
        else:
            self.enpassant_possible = ()

        # Nước đi castle(nhập thành)
        if move.is_castle_move:
            if move.end_col - move.start_col == 2:  # nhập thành cánh vua
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][
                    move.end_col + 1]  # di chuyển xe tới vị trí mới
                self.board[move.end_row][move.end_col + 1] = '--'  # xóa vị trí cũ quân xe
            else:  # nhập thành cánh hậu
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][
                    move.end_col - 2]  # di chuyển xe tới vị trí mới
                self.board[move.end_row][move.end_col - 2] = '--'  # xóa vị trí cũ quân xe

        self.enpassant_possible_log.append(self.enpassant_possible)

        # cập nhật quyền thực hiện Castle sau mỗi nước đi
        self.updateCastleRights(move)
        self.castle_rights_log.append(CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                                   self.current_castling_rights.wqs, self.current_castling_rights.bqs))

    def undoMove(self):
        """
        Undo the last move
        """
        if len(self.move_log) != 0:  # kiểm tra xem có nước đi undo ko
            move = self.move_log.pop()#lấy nước đi cuối cùng
            self.board[move.start_row][move.start_col] = move.piece_moved#đặt lại quân vừa đánh vào vị trí start
            self.board[move.end_row][move.end_col] = move.piece_captured#đặt lại quân bị ăn vào vị trí đích
            self.white_to_move = not self.white_to_move  # đảo lượt chơi
            # cập nhật lại vị trí quân vua
            if move.piece_moved == "wK":
                self.white_king_location = (move.start_row, move.start_col)
            elif move.piece_moved == "bK":
                self.black_king_location = (move.start_row, move.start_col)
            # undo nước đi enpassant
            if move.is_enpassant_move:
                self.board[move.end_row][move.end_col] = "--"  # leave landing square blank
                self.board[move.start_row][move.end_col] = move.piece_captured
            #undo danh sách nước đi enpassant hợp lệ
            self.enpassant_possible_log.pop()
            self.enpassant_possible = self.enpassant_possible_log[-1]

            # undo danh sách quyền castle
            self.castle_rights_log.pop()  # get rid of the new castle rights from the move we are undoing
            self.current_castling_rights = self.castle_rights_log[-1]  # set the current castle rights to the last one in the list
            # undo nước đi nhập thành
            if move.is_castle_move:
                if move.end_col - move.start_col == 2:  # king-side
                    self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                    self.board[move.end_row][move.end_col - 1] = '--'
                else:  # queen-side
                    self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                    self.board[move.end_row][move.end_col + 1] = '--'
            #đánh dấu trò chơi chưa kết thúc
            self.checkmate = False
            self.stalemate = False

#cập nhật quyền thực hiện castle
    def updateCastleRights(self, move):
        """
        Update the castle rights given the move
        """
        if move.piece_captured == "wR":#nếu xe trắng bị mất
            if move.end_col == 0:  # nếu là xe trắng trái
                self.current_castling_rights.wqs = False
            elif move.end_col == 7:  # nếu là xe trắng phải
                self.current_castling_rights.wks = False
        #ngược lại tương tự cho quân đen
        elif move.piece_captured == "bR":
            if move.end_col == 0:  #trái
                self.current_castling_rights.bqs = False
            elif move.end_col == 7:  #phải
                self.current_castling_rights.bks = False
        #nếu vua hoặc xe di chuyển
        if move.piece_moved == 'wK':#vua trắng
            self.current_castling_rights.wqs = False
            self.current_castling_rights.wks = False
        elif move.piece_moved == 'bK':#vua đen
            self.current_castling_rights.bqs = False
            self.current_castling_rights.bks = False
        elif move.piece_moved == 'wR':#xe trắng
            if move.start_row == 7:
                if move.start_col == 0:  # xe trái trắng
                    self.current_castling_rights.wqs = False
                elif move.start_col == 7:  # xe phải trắng
                    self.current_castling_rights.wks = False
        elif move.piece_moved == 'bR':#xe đen
            if move.start_row == 0:
                if move.start_col == 0:  #xe trái đen
                    self.current_castling_rights.bqs = False
                elif move.start_col == 7:  #xe phải đen
                    self.current_castling_rights.bks = False



#Lấy nước đi hợp lệ
    def getValidMoves(self):
        """
        All moves considering checks.
        """
        #khởi tạo 1 bản sao castle right
        temp_castle_rights = CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                          self.current_castling_rights.wqs, self.current_castling_rights.bqs)
        # advanced algorithm
        moves = []
        self.in_check, self.pins, self.checks = self.checkForPinsAndChecks()#hàm kiểm tra chiếu
        #xác định vị trí của vua
        if self.white_to_move:
            king_row = self.white_king_location[0]
            king_col = self.white_king_location[1]
        else:
            king_row = self.black_king_location[0]
            king_col = self.black_king_location[1]

        #di chuyển vua hợp lệ trong trường hợp đang bị chiếu
        if self.in_check:#nếu đang bị chiếu 
            if len(self.checks) == 1:  # nếu có 1 quân chiếu thì lấy quân khác chặn hoặc di chuyển quân vua
                moves = self.getAllPossibleMoves()#lấy ds nc đi
                check = self.checks[0]  # lấy thông tin quân đang chiếu
                check_row = check[0]
                check_col = check[1]
                piece_checking = self.board[check_row][check_col]
                valid_squares = []  # khởi tạo ds nc di chuyển hợp lệ chặn chiếu
                
                #nếu là con mã đang chiếu thì chỉ có thể bị ăn chứ không chặn được
                if piece_checking[1] == "N":
                    valid_squares = [(check_row, check_col)]

                #tính toán nước đi hợp lệ nước đi hợp cho vua   
                else:
                    for i in range(1, 8):
                        valid_square = (king_row + check[2] * i,king_col + check[3] * i)  # check[2] and check[3] are the check directions
                        valid_squares.append(valid_square)
                        if valid_square[0] == check_row and valid_square[1] == check_col:  # once you get to piece and check
                            break
                # loại bỏ nước đi mà không giúp hết bị chiếu
                for i in range(len(moves) - 1, -1, -1):  # duyệt ds
                    if moves[i].piece_moved[1] != "K":  # vua di chuyển hoặc được che để hết chiếu
                        if not (moves[i].end_row, moves[i].end_col) in valid_squares: 
                            moves.remove(moves[i])
            #nếu có 2 quân chiếu trở lên thì vua phải di chuyển
            else:  
                self.getKingMoves(king_row, king_col, moves)
        #nếu không bị chiếu
        else:  
            moves = self.getAllPossibleMoves()
            if self.white_to_move:
                self.getCastleMoves(self.white_king_location[0], self.white_king_location[1], moves)
            else:
                self.getCastleMoves(self.black_king_location[0], self.black_king_location[1], moves)

        #kiểm tra tình trạng kêt thúc trò chơi
        if len(moves) == 0:
            if self.inCheck():
                self.checkmate = True
            else:
                # TODO stalemate on repeated moves
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False

        self.current_castling_rights = temp_castle_rights
        return moves

#kiểm tra chiếu
    def inCheck(self):
        """
        Determine if a current player is in check
        """
        if self.white_to_move:
            return self.squareUnderAttack(self.white_king_location[0], self.white_king_location[1])
        else:
            return self.squareUnderAttack(self.black_king_location[0], self.black_king_location[1])

#kiểm tra 1 ô có bị tấn công hay không
    def squareUnderAttack(self, row, col):
        """
        Determine if enemy can attack the square row col
        """
        self.white_to_move = not self.white_to_move  # switch to opponent's point of view
        opponents_moves = self.getAllPossibleMoves()
        self.white_to_move = not self.white_to_move
        for move in opponents_moves:
            if move.end_row == row and move.end_col == col:  # square is under attack
                return True
        return False

#lấy các nước đi hợp lệ
    def getAllPossibleMoves(self):
        """
        All moves without considering checks.
        """
        moves = []
        for row in range(len(self.board)):
            for col in range(len(self.board[row])):
                turn = self.board[row][col][0]
                if (turn == "w" and self.white_to_move) or (turn == "b" and not self.white_to_move):#nếu tới lượt và đó là quân mình
                    piece = self.board[row][col][1]
                    self.moveFunctions[piece](row, col, moves)  # di chuyển 
        return moves


#kiểm tra bị chặn và chiếu
    def checkForPinsAndChecks(self):
        pins = []  # lưu trữ các ô bị chặn
        checks = []  # lưu trữ các quân đang chiếu
        in_check = False
        #chỉ định màu quân cờ dc phép đi cho lượt hiện tại
        if self.white_to_move:
            enemy_color = "b"
            ally_color = "w"
            start_row = self.white_king_location[0]
            start_col = self.white_king_location[1]
        else:
            enemy_color = "w"
            ally_color = "b"
            start_row = self.black_king_location[0]
            start_col = self.black_king_location[1]
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))#ds các hướng cần kiểm tra 
        #vòng lặp kiểm tra các hướng
        for j in range(len(directions)):
            direction = directions[j]
            possible_pin = ()  
            for i in range(1, 8):
                end_row = start_row + direction[0] * i
                end_col = start_col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                    end_piece = self.board[end_row][end_col]#lấy thông tin ô đích
                    if end_piece[0] == ally_color and end_piece[1] != "K":#kiểm tra ô đích có phải quân phe mình ko (ko phải quân vua)
                        if possible_pin == ():  # nếu có 1 quân mình giữa quân địch và vua mình thì bị kẹt
                            possible_pin = (end_row, end_col, direction[0], direction[1])
                        else:  #Có 2 quân thì ko bị kẹt 
                            break
                    #kiểm tra xem có quân cờ nào đang tấn công quân vua
                    elif end_piece[0] == enemy_color:
                        enemy_type = end_piece[1]
                        # Có 5 loại tấn công ở ô đích gồm: xe, tượng, tốt, hậu, vua
                        # 1.) orthogonally away from king and piece is a rook
                        # 2.) diagonally away from king and piece is a bishop
                        # 3.) 1 square away diagonally from king and piece is a pawn
                        # 4.) any direction and piece is a queen
                        # 5.) any direction 1 square away and piece is a king
                        if (0 <= j <= 3 and enemy_type == "R") or (4 <= j <= 7 and enemy_type == "B") or (i == 1 and enemy_type == "p" and ((enemy_color == "w" and 6 <= j <= 7) or (enemy_color == "b" and 4 <= j <= 5))) or (enemy_type == "Q") or (i == 1 and enemy_type == "K"):
                            if possible_pin == ():  # nếu không có nước nào chặn
                                in_check = True
                                checks.append((end_row, end_col, direction[0], direction[1]))#thêm thông tin
                                break
                            else:  # nếu có nước chặn
                                pins.append(possible_pin)
                                break
                        else:  # nếu ko chiếu
                            break
                else:#nếu ô đích ra khỏi bàn cờ
                    break  # off board
        
        #kiểm tra quân mã 
        knight_moves = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2), (1, -2))
        for move in knight_moves:
            end_row = start_row + move[0]
            end_col = start_col + move[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] == enemy_color and end_piece[1] == "N":  # nếu ngựa đối phương tấn công vua
                    in_check = True
                    checks.append((end_row, end_col, move[0], move[1]))
        return in_check, pins, checks



    def getPawnMoves(self, row, col, moves):
        """
        Get all the pawn moves for the pawn located at row, col and add the moves to the list.
        """
        #khởi tạo
        piece_pinned = False
        pin_direction = ()
        #xem quân tốt này có đang pin tương đối, nếu có lấy hướng pin
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
        #set thông tin di chuyển cho quân tốt khi bắt đầu chơi
        if self.white_to_move:
            move_amount = -1
            start_row = 6
            enemy_color = "b"
            king_row, king_col = self.white_king_location#update vua trắng
        else:
            move_amount = 1
            start_row = 1
            enemy_color = "w"
            king_row, king_col = self.black_king_location#update vua đen
         
        #di chuyển tốt
        if self.board[row + move_amount][col] == "--":  # nếu ko bị chặn
            if not piece_pinned or pin_direction == (move_amount, 0):
                moves.append(Move((row, col), (row + move_amount, col), self.board))#di chuyển theo lên trc 1 ô
                if row == start_row and self.board[row + 2 * move_amount][col] == "--":  # di chuyển 2 ô
                    moves.append(Move((row, col), (row + 2 * move_amount, col), self.board))

        #kiểm tra xem có thể ăn quân ko    
        if col - 1 >= 0:  # kiểm tra ăn quân bên trái
            if not piece_pinned or pin_direction == (move_amount, -1):#kiểm tra có bị chặn ko
                if self.board[row + move_amount][col - 1][0] == enemy_color:#nếu có quân thì có thể ăn
                    moves.append(Move((row, col), (row + move_amount, col - 1), self.board))
                if (row + move_amount, col - 1) == self.enpassant_possible:#kiểm tra nước enpassant
                    attacking_piece = blocking_piece = False
                    if king_row == row:#nếu vua nằm cùng hàng 
                        if king_col < col:  # vua bên trái tốt
                            # inside: between king and the pawn;
                            # outside: between pawn and border;
                            inside_range = range(king_col + 1, col - 1)
                            outside_range = range(col + 1, 8)
                        else:  # nếu vua bên phải tốt
                            inside_range = range(king_col - 1, col, -1)
                            outside_range = range(col - 2, -1, -1)
                        for i in inside_range:#nếu có quân nào cản ở giữa
                            if self.board[row][i] != "--":  # some piece beside en-passant pawn blocks
                                blocking_piece = True
                        for i in outside_range:#nếu có quân xe hoặc hâu cùng hàng thì nc đi enpassant ko hợp lện
                            square = self.board[row][i]
                            if square[0] == enemy_color and (square[1] == "R" or square[1] == "Q"):
                                attacking_piece = True
                            elif square != "--":
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:#nếu không bị chặn hay bị chiếu, enpassant hợp lệ
                        moves.append(Move((row, col), (row + move_amount, col - 1), self.board, is_enpassant_move=True))
        #tương tự cho bên phải
        if col + 1 <= 7:  
            if not piece_pinned or pin_direction == (move_amount, +1):
                if self.board[row + move_amount][col + 1][0] == enemy_color:
                    moves.append(Move((row, col), (row + move_amount, col + 1), self.board))
                if (row + move_amount, col + 1) == self.enpassant_possible:
                    attacking_piece = blocking_piece = False
                    if king_row == row:
                        if king_col < col:  # king is left of the pawn
                            # inside: between king and the pawn;
                            # outside: between pawn and border;
                            inside_range = range(king_col + 1, col)
                            outside_range = range(col + 2, 8)
                        else:  # king right of the pawn
                            inside_range = range(king_col - 1, col + 1, -1)
                            outside_range = range(col - 1, -1, -1)
                        for i in inside_range:
                            if self.board[row][i] != "--":  # some piece beside en-passant pawn blocks
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[row][i]
                            if square[0] == enemy_color and (square[1] == "R" or square[1] == "Q"):
                                attacking_piece = True
                            elif square != "--":
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move((row, col), (row + move_amount, col + 1), self.board, is_enpassant_move=True))



#di chuyển xe
    def getRookMoves(self, row, col, moves):
        """
        Get all the rook moves for the rook located at row, col and add the moves to the list.
        """
        #khởi tạo quân xe chưa bị pin và ds rỗng
        piece_pinned = False
        pin_direction = ()

        #duyệt ds và kiểm tra quân xe có bị pin tương đối hay không
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])#lưu trữ hướng pin
                if self.board[row][col][1] != "Q":  # nếu quân đối phương bắt ko phải quân hậu và quân xe đang chặn lại hành động đó thì ko sao(quân hậu> quân xe)
                    self.pins.remove(self.pins[i])
                break

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))  # up, left, down, right
        enemy_color = "b" if self.white_to_move else "w"
        #duyệt các hướng đi
        for direction in directions:
            for i in range(1, 8):
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:  # kiểm tra ô đích có trong bàn cờ ko
                    if not piece_pinned or pin_direction == direction or pin_direction == (-direction[0], -direction[1]):#nếu ko bị pinpin
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":  # nếu ô đích trống thì di chuyển
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:  # nếu có địch thì ăn
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                            break
                        else:  # friendly piece
                            break
                else:  # off board
                    break

#di chuyển mã
    def getKnightMoves(self, row, col, moves):
        """
        Get all the knight moves for the knight located at row col and add the moves to the list.
        """
        #kiểm tra pin tương đối
        piece_pinned = False
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:#nếu mã bị bin thì đi bình thường
                piece_pinned = True
                self.pins.remove(self.pins[i])
                break

        knight_moves = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2),
                        (1, -2))  # up/left up/right right/up right/down down/left down/right left/up left/down
        ally_color = "w" if self.white_to_move else "b"
        #duyệt danh sách
        for move in knight_moves:
            end_row = row + move[0]
            end_col = col + move[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:#kiểm tra có nằm trong bàn cờ không
                if not piece_pinned:#nếu không bị pin
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] != ally_color:  # nếu có địch hoặc rỗng
                        moves.append(Move((row, col), (end_row, end_col), self.board))

#di chuyển tịnh
    def getBishopMoves(self, row, col, moves):
        """
        Get all the bishop moves for the bishop located at row col and add the moves to the list.
        """
        piece_pinned = False
        pin_direction = ()
        #kiểm tra pin tương đối
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
        
        #di chuyển
        directions = ((-1, -1), (-1, 1), (1, 1), (1, -1))  # diagonals: up/left up/right down/right down/left
        enemy_color = "b" if self.white_to_move else "w"
        for direction in directions:
            for i in range(1, 8):
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:  # check if the move is on board
                    if not piece_pinned or pin_direction == direction or pin_direction == ( -direction[0], -direction[1]):#nếu bị pin hoặ bị pin nhưng vẫn di chuyển theo được dc chéo
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":  # nếu rỗng thì đi
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:  # nếu có địch thì ăn
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                            break
                        else:  # friendly piece
                            break
                else:  # off board
                    break

#di chuyển hậu
    def getQueenMoves(self, row, col, moves):
        """
        Get all the queen moves for the queen located at row col and add the moves to the list.
        """
        self.getBishopMoves(row, col, moves)
        self.getRookMoves(row, col, moves)

#di chuyển vua
    def getKingMoves(self, row, col, moves):
        """
        Get all the king moves for the king located at row col and add the moves to the list.
        """
        row_moves = (-1, -1, -1, 0, 0, 1, 1, 1)
        col_moves = (-1, 0, 1, -1, 1, -1, 0, 1)
        ally_color = "w" if self.white_to_move else "b"
        #di chuyển
        for i in range(8):
            end_row = row + row_moves[i]
            end_col = col + col_moves[i]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color:  #nếu rỗng hoặc có địch
                    # place king on end square and check for checks
                    if ally_color == "w":
                        self.white_king_location = (end_row, end_col)
                    else:
                        self.black_king_location = (end_row, end_col)
                    in_check, pins, checks = self.checkForPinsAndChecks()
                    if not in_check:
                        moves.append(Move((row, col), (end_row, end_col), self.board))
                    # place king back on original location
                    if ally_color == "w":#nếu bị chiếu thì quay về nước cũ
                        self.white_king_location = (row, col)
                    else:
                        self.black_king_location = (row, col)

    def getCastleMoves(self, row, col, moves):
        """
        Generate all valid castle moves for the king at (row, col) and add them to the list of moves.
        """
        if self.squareUnderAttack(row, col):#nếu vua bị chiếu thì không nhập thành
            return  # can't castle while in check
        if (self.white_to_move and self.current_castling_rights.wks) or (
                not self.white_to_move and self.current_castling_rights.bks):#nếu nhập thành cánh vua thỏa mãn
            self.getKingsideCastleMoves(row, col, moves)
        if (self.white_to_move and self.current_castling_rights.wqs) or (
                not self.white_to_move and self.current_castling_rights.bqs):#nếu nhập thành cánh hậu thỏa mãn
            self.getQueensideCastleMoves(row, col, moves)

#nhập thành cánh vua
    def getKingsideCastleMoves(self, row, col, moves):
        if self.board[row][col + 1] == '--' and self.board[row][col + 2] == '--':#nếu cánh vua rỗng
            if not self.squareUnderAttack(row, col + 1) and not self.squareUnderAttack(row, col + 2):#và 2 ô đó ko bị chiếu
                moves.append(Move((row, col), (row, col + 2), self.board, is_castle_move=True))

#nhập thành cánh hậu
    def getQueensideCastleMoves(self, row, col, moves):
        if self.board[row][col - 1] == '--' and self.board[row][col - 2] == '--' and self.board[row][col - 3] == '--':
            if not self.squareUnderAttack(row, col - 1) and not self.squareUnderAttack(row, col - 2):
                moves.append(Move((row, col), (row, col - 2), self.board, is_castle_move=True))


class CastleRights:
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


class Move:
    # in chess, fields on the board are described by two symbols, one of them being number between 1-8 (which is corresponding to rows)
    # and the second one being a letter between a-f (corresponding to columns), in order to use this notation we need to map our [row][col] coordinates
    # to match the ones used in the original chess game
    ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4,
                     "5": 3, "6": 2, "7": 1, "8": 0}#chuyển từ hàng bàn cờ sang hàng trên screen
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}#chuyển ngược lại
    files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3,
                     "e": 4, "f": 5, "g": 6, "h": 7}#chuyển từ chữ sang cột
    cols_to_files = {v: k for k, v in files_to_cols.items()}#ngược lại

    def __init__(self, start_square, end_square, board, is_enpassant_move=False, is_castle_move=False):
        #khởi tạo các biến
        self.start_row = start_square[0]
        self.start_col = start_square[1]
        self.end_row = end_square[0]
        self.end_col = end_square[1]
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]
        # pawn promotion
        self.is_pawn_promotion = (self.piece_moved == "wp" and self.end_row == 0) or (
                self.piece_moved == "bp" and self.end_row == 7)
        # en passant
        self.is_enpassant_move = is_enpassant_move
        if self.is_enpassant_move:
            self.piece_captured = "wp" if self.piece_moved == "bp" else "bp"
        # castle move
        self.is_castle_move = is_castle_move

        self.is_capture = self.piece_captured != "--"
        self.moveID = self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col#mã số xác định mỗi nước đi

    def __eq__(self, other):
        """
        Overriding the equals method.
        """
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

#update khi 1 thao tác xảy ra
    def getChessNotation(self):
        if self.is_pawn_promotion:#kiểm tra phong tốt
            return self.getRankFile(self.start_row, self.start_col) + self.getRankFile(self.end_row, self.end_col) + "Q"
        if self.is_castle_move:#kiểm tra nhập thành
            if self.end_col == 1:
                return "0-0-0"
            else:
                return "0-0"
        if self.is_enpassant_move:#kiểm tra nước enpassant
            return self.getRankFile(self.start_row, self.start_col)[0] + "x" + self.getRankFile(self.end_row,
                                                                                                self.end_col) + " e.p."
        return self.getRankFile(self.start_row, self.start_col) + self.getRankFile(self.end_row, self.end_col)

        # TODO Disambiguating moves

    def getRankFile(self, row, col):
        return self.cols_to_files[col] + self.rows_to_ranks[row]

    def __str__(self):
        if self.is_castle_move:
            return "0-0" if self.end_col == 6 else "0-0-0"
 
        start_square = self.getRankFile(self.start_row, self.start_col)
        end_square = self.getRankFile(self.end_row, self.end_col)

        if self.piece_moved[1] == "p":
            if self.is_capture:
                return start_square + end_square
            else:
                return end_square + "Q" if self.is_pawn_promotion else start_square + end_square

       
        return  start_square + end_square