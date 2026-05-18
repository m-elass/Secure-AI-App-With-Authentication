import "react"
import {useState, useEffect} from "react"
import {MCQChallenge} from "../challenge/MCQChallenge.jsx";
import {useApi} from "../utils/api.js";

export function HistoryPanel() {
    const {makeRequest} = useApi()
    const [history, setHistory] = useState([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState(null)
    const [filter, setFilter] = useState("all")

    useEffect(() => {
        fetchHistory()
    }, [])

    const fetchHistory = async () => {
        setIsLoading(true)
        setError(null)
        try {
            const data = await makeRequest("my-history")
            setHistory(data.challenges || [])
        } catch (err) {
            setError("No se pudo cargar el historial.")
        } finally {
            setIsLoading(false)
        }
    }

    if (isLoading) {
        return (
            <div className="loading">
                <div className="loading-spinner" aria-hidden="true"></div>
                <div className="loading-text">Cargando historial...</div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="challenge-container">
                <div className="error-message" role="alert">
                    <span aria-hidden="true">⚠</span>
                    <span>{error}</span>
                </div>
                <button onClick={fetchHistory} className="generate-button" style={{marginTop: "1rem"}}>
                    Reintentar
                </button>
            </div>
        )
    }

    const counts = {
        all: history.length,
        easy: history.filter(c => (c.difficulty || "").toLowerCase() === "easy").length,
        medium: history.filter(c => (c.difficulty || "").toLowerCase() === "medium").length,
        hard: history.filter(c => (c.difficulty || "").toLowerCase() === "hard").length,
    }

    const filtered = filter === "all"
        ? history
        : history.filter(c => (c.difficulty || "").toLowerCase() === filter)

    return (
        <div className="history-panel">
            <div className="history-header">
                <div>
                    <h2 className="section-title">Tu historial</h2>
                    <p className="section-subtitle" style={{margin: 0}}>
                        Todas las preguntas que has generado, con sus respuestas correctas.
                    </p>
                </div>
            </div>

            {history.length > 0 && (
                <div className="difficulty-pills" style={{marginBottom: "2rem"}}>
                    <button
                        type="button"
                        className={`diff-pill ${filter === "all" ? "selected" : ""}`}
                        style={{"--pill-color": "var(--accent)"}}
                        onClick={() => setFilter("all")}
                    >
                        <span className="diff-pill-name">
                            <span className="diff-pill-dot" aria-hidden="true"></span>
                            Todas
                        </span>
                        <span className="diff-pill-desc">{counts.all} preguntas</span>
                    </button>
                    <button
                        type="button"
                        className={`diff-pill easy ${filter === "easy" ? "selected" : ""}`}
                        onClick={() => setFilter("easy")}
                    >
                        <span className="diff-pill-name">
                            <span className="diff-pill-dot" aria-hidden="true"></span>
                            Fácil
                        </span>
                        <span className="diff-pill-desc">{counts.easy} preguntas</span>
                    </button>
                    <button
                        type="button"
                        className={`diff-pill medium ${filter === "medium" ? "selected" : ""}`}
                        onClick={() => setFilter("medium")}
                    >
                        <span className="diff-pill-name">
                            <span className="diff-pill-dot" aria-hidden="true"></span>
                            Medio
                        </span>
                        <span className="diff-pill-desc">{counts.medium} preguntas</span>
                    </button>
                    <button
                        type="button"
                        className={`diff-pill hard ${filter === "hard" ? "selected" : ""}`}
                        onClick={() => setFilter("hard")}
                    >
                        <span className="diff-pill-name">
                            <span className="diff-pill-dot" aria-hidden="true"></span>
                            Difícil
                        </span>
                        <span className="diff-pill-desc">{counts.hard} preguntas</span>
                    </button>
                </div>
            )}

            {history.length === 0 ? (
                <div className="history-empty">
                    <div className="history-empty-icon" aria-hidden="true">📭</div>
                    <p style={{fontSize: "1rem", marginBottom: "0.5rem", color: "var(--text-secondary)"}}>
                        Todavía no has generado ninguna pregunta
                    </p>
                    <p style={{fontSize: "0.85rem"}}>
                        Vuelve al generador y prueba a hacer la primera.
                    </p>
                </div>
            ) : filtered.length === 0 ? (
                <div className="history-empty">
                    <p style={{color: "var(--text-secondary)"}}>
                        Aún no hay preguntas de esta dificultad.
                    </p>
                </div>
            ) : (
                <div className="history-list">
                    {filtered.map((challenge) => (
                        <MCQChallenge
                            challenge={challenge}
                            key={challenge.id}
                            showExplanation
                        />
                    ))}
                </div>
            )}
        </div>
    )
}
