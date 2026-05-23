import "react"
import {useState, useEffect} from "react"
import {MCQChallenge} from "../challenge/MCQChallenge.jsx"
import {useApi} from "../utils/api.js"
import {useSubject} from "../utils/SubjectContext.jsx"

export function HistoryPanel() {
    const {makeRequest} = useApi()
    const {activeSubject, activeMeta, subjects} = useSubject()
    const [history, setHistory] = useState([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState(null)
    const [difficultyFilter, setDifficultyFilter] = useState("all")
    const [showAllSubjects, setShowAllSubjects] = useState(false)

    // Recargamos historial cuando cambia la asignatura o el toggle global
    useEffect(() => {
        fetchHistory()
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeSubject, showAllSubjects])

    const fetchHistory = async () => {
        setIsLoading(true)
        setError(null)
        try {
            const params = showAllSubjects ? "" : `?subject=${encodeURIComponent(activeSubject)}`
            const data = await makeRequest("my-history" + params)
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

    const filtered = difficultyFilter === "all"
        ? history
        : history.filter(c => (c.difficulty || "").toLowerCase() === difficultyFilter)

    return (
        <div className="history-panel">
            <div className="history-header">
                <div>
                    <h2 className="section-title">Tu historial</h2>
                    <p className="section-subtitle" style={{margin: 0}}>
                        {showAllSubjects
                            ? "Todas las preguntas que has generado, de cualquier asignatura."
                            : <>Tus preguntas de <strong>{activeMeta?.full_name || activeMeta?.name}</strong>.</>}
                    </p>
                </div>

                {subjects.length > 1 && (
                    <label className="subject-toggle">
                        <input
                            type="checkbox"
                            checked={showAllSubjects}
                            onChange={(e) => setShowAllSubjects(e.target.checked)}
                        />
                        <span>Ver todas las asignaturas</span>
                    </label>
                )}
            </div>

            {history.length > 0 && (
                <div className="difficulty-pills" style={{marginBottom: "2rem"}}>
                    <button
                        type="button"
                        className={`diff-pill ${difficultyFilter === "all" ? "selected" : ""}`}
                        style={{"--pill-color": "var(--accent)"}}
                        onClick={() => setDifficultyFilter("all")}
                    >
                        <span className="diff-pill-name">
                            <span className="diff-pill-dot" aria-hidden="true"></span>
                            Todas
                        </span>
                        <span className="diff-pill-desc">{counts.all} preguntas</span>
                    </button>
                    <button
                        type="button"
                        className={`diff-pill easy ${difficultyFilter === "easy" ? "selected" : ""}`}
                        onClick={() => setDifficultyFilter("easy")}
                    >
                        <span className="diff-pill-name">
                            <span className="diff-pill-dot" aria-hidden="true"></span>
                            Fácil
                        </span>
                        <span className="diff-pill-desc">{counts.easy} preguntas</span>
                    </button>
                    <button
                        type="button"
                        className={`diff-pill medium ${difficultyFilter === "medium" ? "selected" : ""}`}
                        onClick={() => setDifficultyFilter("medium")}
                    >
                        <span className="diff-pill-name">
                            <span className="diff-pill-dot" aria-hidden="true"></span>
                            Medio
                        </span>
                        <span className="diff-pill-desc">{counts.medium} preguntas</span>
                    </button>
                    <button
                        type="button"
                        className={`diff-pill hard ${difficultyFilter === "hard" ? "selected" : ""}`}
                        onClick={() => setDifficultyFilter("hard")}
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
                        {!showAllSubjects && <> de <strong>{activeMeta?.name}</strong></>}
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