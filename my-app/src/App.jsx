import React, { useState, useEffect, useRef } from 'react';
import './App.css';

// Pose image mapping
const poseImages = {
  RAISE_HANDS: '/images/RAISE_HAND.jpg',
  SIU: '/images/SIU.jpg',
  DOG_POSE: '/images/DOG_POSE.jpg',
  MON_POSE: '/images/MON_POSE.jpg',
  FLEXING: '/images/FLEXING.jpg',
  ABSOLUTE: '/images/ABSOLUTE.jpg',
  DYNAMIC: '/images/DYNAMIC.jpg',
  KAWAII: '/images/KAWAII.jpg',
  KHABY_LAME: '/images/KHABY_LAME.jpg',
  MON_POSE2: '/images/MON_POSE2.jpg',
  
};

// Predefined meme paths
const SUCCESS_MEMES = [
  '/memes/success/0.jpg',
  '/memes/success/1.jpg'
];

const FAIL_MEMES = [
  '/memes/fail/0.jpg',
  '/memes/fail/1.jpg',
  '/memes/fail/2.jpg',
  '/memes/fail/3.jpg'
];

const PoseGameSimple = () => {
  const [gameState, setGameState] = useState({
    currentPose: '',
    currentScore: 0,
    timeLeft: 3,
    successCount: 0,
    failCount: 0,
    result: null,
    isPlaying: false,
    showEndDashboard: false
  });

  const [globalTimeLeft, setGlobalTimeLeft] = useState(30);
  const [firstFrameSeen, setFirstFrameSeen] = useState(false);
  const [cooldownActive, setCooldownActive] = useState(false);
  const [cooldownMeme, setCooldownMeme] = useState(null);
  const [isStarting, setIsStarting] = useState(false);
  const [startCountdown, setStartCountdown] = useState(3);
  const [successIndex, setSuccessIndex] = useState(0);
  const [failIndex, setFailIndex] = useState(0);

  // Audio refs
  const audioRef = useRef(null);
  const failAudioRef = useRef(null); // fail.mp3 for fail
  const incredibleAudioRef = useRef(null); // incredible.mp3 at end

  const videoRef = useRef(null);
  const globalTimerRef = useRef(null);
  const prevResultRef = useRef(null);

  const startGame = async () => {
    setIsStarting(true);
    setStartCountdown(3);
    
    // Stop the incredible sound if it's playing
    if (incredibleAudioRef.current) {
      incredibleAudioRef.current.pause();
      incredibleAudioRef.current.currentTime = 0;
    }

    try {
      await audioRef.current?.play();
    } catch (err) {
      console.warn('Background audio autoplay blocked:', err);
    }

    const countdown = setInterval(() => {
      setStartCountdown(prev => {
        if (prev <= 1) {
          clearInterval(countdown);
          setIsStarting(false);
          fetch('http://localhost:5000/start_game', { method: 'POST' }).then(() => {
            setFirstFrameSeen(false);
            setGlobalTimeLeft(30);
            setCooldownActive(false);
            setCooldownMeme(null);
            setGameState(gs => ({ ...gs, isPlaying: true, showEndDashboard: false }));
          });
        }
        return prev - 1;
      });
    }, 1000);
  };

  const endGame = async () => {
    await fetch('http://localhost:5000/stop_game', { method: 'POST' });
    audioRef.current?.pause();
    audioRef.current.currentTime = 0;

    clearInterval(globalTimerRef.current);

    // Play end game sound
    try {
      incredibleAudioRef.current.currentTime = 0;
      await incredibleAudioRef.current.play();
    } catch (err) {
      console.warn('Failed to play end sound:', err);
    }

    // Set isPlaying to false first to stop state updates
    setGameState(gs => ({ ...gs, isPlaying: false }));
    // Then show the end dashboard
    setGameState(gs => ({ ...gs, showEndDashboard: true }));
  };

  useEffect(() => {
    if (!gameState.isPlaying) return;

    globalTimerRef.current = setInterval(() => {
      setGlobalTimeLeft(prev => {
        if (prev <= 1) {
          clearInterval(globalTimerRef.current);
          endGame();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(globalTimerRef.current);
  }, [gameState.isPlaying]);

  useEffect(() => {
    if (!gameState.isPlaying) return;

    const interval = setInterval(async () => {
      const res = await fetch('http://localhost:5000/game_state');
      const data = await res.json();

      const currentResult = data.result;

      if (prevResultRef.current !== currentResult && currentResult !== null) {
        const isSuccess = currentResult === 'SUCCESS';
        let nextMeme;

        if (isSuccess) {
          setSuccessIndex(prev => {
            const newIndex = (prev + 1) % SUCCESS_MEMES.length;
            nextMeme = SUCCESS_MEMES[newIndex];
            return newIndex;
          });
        } else {
          // Play cat.mp3 when user fails to make a pose
          try {
            failAudioRef.current.currentTime = 0;
            await failAudioRef.current.play();
          } catch (err) {
            console.warn('Failed to play fail sound:', err);
          }

          setFailIndex(prev => {
            const newIndex = (prev + 1) % FAIL_MEMES.length;
            nextMeme = FAIL_MEMES[newIndex];
            return newIndex;
          });
        }

        setCooldownMeme(nextMeme);
        setCooldownActive(true);

        setTimeout(() => {
          setCooldownActive(false);
          setCooldownMeme(null);
        }, 2000);
      }

      prevResultRef.current = currentResult;

      // Only update game state if the game is still playing
      if (gameState.isPlaying) {
        setGameState(gs => ({
          ...gs,
          currentPose: data.current_pose,
          currentScore: data.current_score,
          timeLeft: cooldownActive ? gs.timeLeft : data.time_left,
          successCount: data.success_count,
          failCount: data.fail_count,
          result: data.result
        }));
      }
    }, 200);

    return () => {
      clearInterval(interval);
      prevResultRef.current = null;
    };
  }, [gameState.isPlaying, cooldownActive]);

  const poseNumber = gameState.successCount + gameState.failCount + 1;

  const renderEndDashboard = () => {
    const totalPoses = gameState.successCount + gameState.failCount;
    const successRate = totalPoses > 0 ? (gameState.successCount / totalPoses) * 100 : 0;

    return (
      <div className="end-dashboard">
        <div className="gigachad-container">
          <img src="/images/GIGACHART.jpg" alt="GIGACHAD" className="gigachad-image" />
        </div>
        <h2>Game Over!</h2>
        <div className="stats-container">
          <div className="stat-box">
            <h3>Total Poses</h3>
            <p>{totalPoses}</p>
          </div>
          <div className="stat-box success">
            <h3>Success</h3>
            <p>{gameState.successCount}</p>
          </div>
          <div className="stat-box fail">
            <h3>Fail</h3>
            <p>{gameState.failCount}</p>
          </div>
          <div className="stat-box">
            <h3>Success Rate</h3>
            <p>{successRate.toFixed(1)}%</p>
          </div>
        </div>
        <div className="performance-message">
          {successRate >= 70 ? (
            <p className="excellent">Excellent! You're a pose master! 🏆</p>
          ) : successRate >= 40 ? (
            <p className="good">Good job! Keep practicing! 💪</p>
          ) : (
            <p className="try-again">Keep trying! You'll get better! 🌟</p>
          )}
        </div>
        <button className="restart-button" onClick={startGame}>
          Play Again
        </button>
      </div>
    );
  };

  return (
    <div className="app-container">
      {/* Background music */}
      <audio ref={audioRef} src="/audio/subway.mp3" preload="auto" loop />

      {/* Sound played on fail */}
      <audio ref={failAudioRef} src="/audio/fail.mp3" preload="auto" />

      {/* End game sound */}
      <audio ref={incredibleAudioRef} src="/audio/incredible.mp3" preload="auto" />

      <div className="game-container">
        {isStarting ? (
          <div className="start-screen" style={{ textAlign: 'center', paddingTop: '30vh' }}>
            <h1 style={{ fontSize: '4rem' }}>Get Ready In...</h1>
            <h2 style={{ fontSize: '6rem', color: '#b47b00' }}>{startCountdown}</h2>
          </div>
        ) : !gameState.isPlaying ? (
          gameState.showEndDashboard ? (
            renderEndDashboard()
          ) : (
            <div className="start-screen">
              <div className="title-container">
                <h1>Poser</h1>
                <img src="/images/poserlogo.png" alt="Poser Logo" className="title-logo" />
              </div>
              <button className="start-button" onClick={startGame}>Start Game</button>
            </div>
          )
        ) : (
          <>

            <div className="game-grid">
              <div className="pose-clue">
                {gameState.currentPose && (
                  <img src={poseImages[gameState.currentPose]} alt={gameState.currentPose} />
                )}
                <p>Follow this silly pose...</p>
              </div>

              <div className="video-container">
                <div className="game-stats">
                  <div className="stat-item"><span className="stat-label">Pose:</span> {poseNumber}</div>
                  <div className="stat-item"><span className="stat-label">Success:</span> {gameState.successCount}</div>
                  <div className="stat-item"><span className="stat-label">Fail:</span> {gameState.failCount}</div>
                  <div className="stat-item"><span className="stat-label">Score:</span> {gameState.currentScore.toFixed(2)}%</div>
                  <div className="stat-item"><span className="stat-label">Time:</span> {globalTimeLeft}s</div>
                  <div className="stat-item timer-display">
                    <span className="stat-label">Pose Timer:</span>
                    <span className={`timer ${gameState.timeLeft <= 1 ? 'urgent' : ''}`}>
                      {gameState.timeLeft.toFixed(1)}s
                    </span>
                  </div>
                </div>

                <div className="video-feed">
                  <img
                    ref={videoRef}
                    src="http://localhost:5000/video_feed"
                    alt="Video Feed"
                    onLoad={() => {
                      if (!firstFrameSeen) setFirstFrameSeen(true);
                    }}
                  />
                </div>

                
              </div>
              

              <div className="end-game-button">
                <button onClick={endGame}>End Game</button>
              </div>
            </div>
            
          </>
        )}
      </div>
    </div>
  );
};

export default PoseGameSimple;