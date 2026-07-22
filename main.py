<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>テトリス - JavaScript Game</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: #121212;
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            overflow: hidden;
        }

        .game-container {
            display: flex;
            gap: 20px;
            background-color: #1e1e1e;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        }

        .board-container {
            position: relative;
            border: 4px solid #333;
            border-radius: 4px;
        }

        canvas {
            display: block;
            background-color: #000;
        }

        .sidebar {
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            width: 160px;
        }

        .info-box {
            background-color: #2a2a2a;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 15px;
        }

        .info-box h2 {
            font-size: 14px;
            color: #aaa;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }

        .info-box p {
            font-size: 24px;
            font-weight: bold;
            color: #00f0f0;
        }

        .controls-hint {
            font-size: 12px;
            color: #888;
            line-height: 1.6;
            margin-top: auto;
        }

        .controls-hint span {
            color: #fff;
            font-weight: bold;
        }

        .overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.85);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            border-radius: 4px;
        }

        .overlay h1 {
            font-size: 28px;
            color: #ff4757;
            margin-bottom: 10px;
        }

        .overlay p {
            font-size: 16px;
            margin-bottom: 20px;
        }

        .btn {
            background-color: #00f0f0;
            color: #000;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.2s, transform 0.1s;
        }

        .btn:hover {
            background-color: #52ffff;
            transform: scale(1.05);
        }

        .btn:active {
            transform: scale(0.98);
        }
    </style>
</head>
<body>

<div class="game-container">
    <div class="board-container">
        <canvas id="tetris" width="240" height="400"></canvas>
        <div id="game-over-screen" class="overlay">
            <h1>GAME OVER</h1>
            <p>Score: <span id="final-score">0</span></p>
            <button class="btn" onclick="resetGame()">再挑戦</button>
        </div>
    </div>

    <div class="sidebar">
        <div>
            <div class="info-box">
                <h2>Score</h2>
                <p id="score">0</p>
            </div>
            <div class="info-box">
                <h2>Lines</h2>
                <p id="lines">0</p>
            </div>
            <div class="info-box">
                <h2>Level</h2>
                <p id="level">1</p>
            </div>
            <div class="info-box">
                <h2>NEXT</h2>
                <canvas id="next" width="80" height="80"></canvas>
            </div>
        </div>

        <div class="controls-hint">
            <p><span>← →</span> : 移動</p>
            <p><span>↑</span> : 回転</p>
            <p><span>↓</span> : ソフトドロップ</p>
            <p><span>Space</span> : ハードドロップ</p>
        </div>
    </div>
</div>

<script>
    const canvas = document.getElementById('tetris');
    const context = canvas.getContext('2d');
    const nextCanvas = document.getElementById('next');
    const nextContext = nextCanvas.getContext('2d');

    const scoreElement = document.getElementById('score');
    const linesElement = document.getElementById('lines');
    const levelElement = document.getElementById('level');
    const finalScoreElement = document.getElementById('final-score');
    const gameOverScreen = document.getElementById('game-over-screen');

    // 1ブロックあたりのピクセルサイズ（240x400 / 10x20）
    const BLOCK_SIZE = 24;
    const ROWS = 20;
    const COLS = 10;

    context.scale(BLOCK_SIZE, BLOCK_SIZE);
    nextContext.scale(20, 20); // Next画面用のスケール

    // テトロミノの色定義
    const COLORS = [
        null,
        '#00f0f0', // I (Cyan)
        '#0000f0', // J (Blue)
        '#f0a000', // L (Orange)
        '#f0f000', // O (Yellow)
        '#00f000', // S (Green)
        '#a000f0', // T (Purple)
        '#f00000'  // Z (Red)
    ];

    // テトロミノの形状定義
    function createPiece(type) {
        if (type === 'I') {
            return [
                [0, 1, 0, 0],
                [0, 1, 0, 0],
                [0, 1, 0, 0],
                [0, 1, 0, 0],
            ];
        } else if (type === 'J') {
            return [
                [0, 2, 0],
                [0, 2, 0],
                [2, 2, 0],
            ];
        } else if (type === 'L') {
            return [
                [0, 3, 0],
                [0, 3, 0],
                [0, 3, 3],
            ];
        } else if (type === 'O') {
            return [
                [4, 4],
                [4, 4],
            ];
        } else if (type === 'S') {
            return [
                [0, 5, 5],
                [5, 5, 0],
                [0, 0, 0],
            ];
        } else if (type === 'T') {
            return [
                [0, 6, 0],
                [6, 6, 6],
                [0, 0, 0],
            ];
        } else if (type === 'Z') {
            return [
                [7, 7, 0],
                [0, 7, 7],
                [0, 0, 0],
            ];
        }
    }

    // ゲーム盤の初期化（空の2次元配列）
    function createMatrix(w, h) {
        const matrix = [];
        while (h--) {
            matrix.push(new Array(w).fill(0));
        }
        return matrix;
    }

    const arena = createMatrix(COLS, ROWS);

    const player = {
        pos: {x: 0, y: 0},
        matrix: null,
        nextMatrix: null,
        score: 0,
        lines: 0,
        level: 1,
    };

    // 衝突判定
    function collide(arena, player) {
        const [m, o] = [player.matrix, player.pos];
        for (let y = 0; y < m.length; ++y) {
            for (let x = 0; x < m[y].length; ++x) {
                if (m[y][x] !== 0 &&
                   (arena[y + o.y] && arena[y + o.y][x + o.x]) !== 0) {
                    return true;
                }
            }
        }
        return false;
    }

    // 盤面固定処理
    function merge(arena, player) {
        player.matrix.forEach((row, y) => {
            row.forEach((value, x) => {
                if (value !== 0) {
                    arena[y + player.pos.y][x + player.pos.x] = value;
                }
            });
        });
    }

    // 描画関係の処理
    function draw() {
        // メインキャンバスのクリア
        context.fillStyle = '#000';
        context.fillRect(0, 0, canvas.width, canvas.height);

        drawMatrix(arena, {x: 0, y: 0}, context);
        drawMatrix(player.matrix, player.pos, context);

        // Nextキャンバスのクリアと描画
        nextContext.fillStyle = '#2a2a2a';
        nextContext.fillRect(0, 0, nextCanvas.width, nextCanvas.height);
        
        if (player.nextMatrix) {
            // 中央に表示するためのオフセット計算
            const offsetX = (4 - player.nextMatrix[0].length) / 2;
            const offsetY = (4 - player.nextMatrix.length) / 2;
            drawMatrix(player.nextMatrix, {x: offsetX, y: offsetY}, nextContext);
        }
    }

    function drawMatrix(matrix, offset, ctx) {
        matrix.forEach((row, y) => {
            row.forEach((value, x) => {
                if (value !== 0) {
                    ctx.fillStyle = COLORS[value];
                    ctx.fillRect(x + offset.x, y + offset.y, 1, 1);

                    // ブロックに立体感を出すグリッド線
                    ctx.lineWidth = 0.05;
                    ctx.strokeStyle = '#ffffff';
                    ctx.strokeRect(x + offset.x, y + offset.y, 1, 1);
                }
            });
        });
    }

    // ライン消去判定処理
    function arenaSweep() {
        let rowCount = 0;
        outer: for (let y = arena.length - 1; y >= 0; --y) {
            for (let x = 0; x < arena[y].length; ++x) {
                if (arena[y][x] === 0) {
                    continue outer;
                }
            }

            const row = arena.splice(y, 1)[0].fill(0);
            arena.unshift(row);
            ++y;

            rowCount++;
        }

        if (rowCount > 0) {
            // スコア計算 (1行:100, 2行:300, 3行:500, 4行:800)
            const lineScores = [0, 100, 300, 500, 800];
            player.score += lineScores[rowCount] * player.level;
            player.lines += rowCount;
            player.level = Math.floor(player.lines / 10) + 1;
            updateScore();
        }
    }

    // プレイヤーの移動処理
    function playerMove(dir) {
        player.pos.x += dir;
        if (collide(arena, player)) {
            player.pos.x -= dir;
        }
    }

    // ピースの生成およびゲームオーバー判断
    function playerReset() {
        const pieces = 'IJLOSTZ';
        if (player.nextMatrix === null) {
            player.nextMatrix = createPiece(pieces[pieces.length * Math.random() | 0]);
        }

        player.matrix = player.nextMatrix;
        player.nextMatrix = createPiece(pieces[pieces.length * Math.random() | 0]);

        player.pos.y = 0;
        player.pos.x = (arena[0].length / 2 | 0) - (player.matrix[0].length / 2 | 0);

        // 発生直後に衝突していればゲームオーバー
        if (collide(arena, player)) {
            gameOver();
        }
    }

    // ソフトドロップ（落下速度の調整）
    function playerDrop() {
        player.pos.y++;
        if (collide(arena, player)) {
            player.pos.y--;
            merge(arena, player);
            arenaSweep();
            playerReset();
        }
        dropCounter = 0;
    }

    // ハードドロップ（一気に一番下まで落とす）
    function playerHardDrop() {
        while (!collide(arena, player)) {
            player.pos.y++;
        }
        player.pos.y--;
        merge(arena, player);
        arenaSweep();
        playerReset();
        dropCounter = 0;
    }

    // 回転（壁蹴り簡易実装含む）
    function playerRotate(dir) {
        const pos = player.pos.x;
        let offset = 1;
        rotate(player.matrix, dir);
        while (collide(arena, player)) {
            player.pos.x += offset;
            offset = -(offset + (offset > 0 ? 1 : -1));
            if (offset > player.matrix[0].length) {
                rotate(player.matrix, -dir);
                player.pos.x = pos;
                return;
            }
        }
    }

    // 行列の転置と反転による回転
    function rotate(matrix, dir) {
        for (let y = 0; y < matrix.length; ++y) {
            for (let x = 0; x < y; ++x) {
                [
                    matrix[x][y],
                    matrix[y][x],
                ] = [
                    matrix[y][x],
                    matrix[x][y],
                ];
            }
        }

        if (dir > 0) {
            matrix.forEach(row => row.reverse());
        } else {
            matrix.reverse();
        }
    }

    // アニメーションループ管理
    let dropCounter = 0;
    let lastTime = 0;
    let isGameOver = false;

    function update(time = 0) {
        if (isGameOver) return;

        const deltaTime = time - lastTime;
        lastTime = time;

        dropCounter += deltaTime;

        // レベルに応じて落下速度を向上 (最小100ms)
        const dropInterval = Math.max(100, 1000 - (player.level - 1) * 100);

        if (dropCounter > dropInterval) {
            playerDrop();
        }

        draw();
        requestAnimationFrame(update);
    }

    function updateScore() {
        scoreElement.innerText = player.score;
        linesElement.innerText = player.lines;
        levelElement.innerText = player.level;
    }

    function gameOver() {
        isGameOver = true;
        finalScoreElement.innerText = player.score;
        gameOverScreen.style.display = 'flex';
    }

    function resetGame() {
        arena.forEach(row => row.fill(0));
        player.score = 0;
        player.lines = 0;
        player.level = 1;
        player.nextMatrix = null;
        isGameOver = false;
        gameOverScreen.style.display = 'none';
        updateScore();
        playerReset();
        update();
    }

    // キー入力監視
    document.addEventListener('keydown', event => {
        if (isGameOver) return;

        if (event.keyCode === 37) { // 左矢印
            playerMove(-1);
        } else if (event.keyCode === 39) { // 右矢印
            playerMove(1);
        } else if (event.keyCode === 40) { // 下矢印
            playerDrop();
        } else if (event.keyCode === 38) { // 上矢印
            playerRotate(1);
        } else if (event.keyCode === 32) { // スペースキー
            event.preventDefault(); // スクロール防止
            playerHardDrop();
        }
    });

    // 初期起動
    gameOverScreen.style.display = 'none';
    playerReset();
    updateScore();
    update();
</script>

</body>
</html>