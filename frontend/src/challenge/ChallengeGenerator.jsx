import "react"
import {useState, useEffect} from "react"
import {MCQChallenge} from "./MCQChallenge.jsx";
import {useApi} from "../utils/api.js"

const DIFFICULTIES = [
    {
        id: "easy",
        name: "Fácil",
        description: "Conceptos básicos: clases, verbos HTTP, JSON",
        className: "easy",
    },
    {
        id: "medium",
        name: "Medio",
        description: "Herencia, REST, sockets, loads vs load",
        className: "medium",
    },
    {
        id: "hard",
        name: "Difícil",
        description: "Análisis de código, traza HTTP, override avanzado",
        className: "hard",
    },
]

// Mensajes rotativos durante la generación para que sea menos aburrido
const LOADING_MESSAGES = [
    "Consultando el temario de PER...",
    "Diseñando distractores plausibles...",
    "Buscando ese bug sutil en el código...",
    "Revisando los apuntes de la URJC...",
    "Repasando exámenes anteriores...",
    "Eligiendo el nivel adecuado de trampa...",
]

export function ChallengeGenerator() {
    const [challenge, setChallenge] = useState(null)
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState(null)
    const [difficulty, setDifficulty] = useState("easy")
    const [quota, setQuota] = useState(null)
    const [loadingMsg, setLoadingMsg] = useState(LOADING_MESSAGES[0])
    const {makeRequest} = useApi()

    useEffect(() => {
        fetchQuota()
    }, [])

    // Rotamos los mensajes de carga cada 1.8s mientras genera
    useEffect(() => {
        if (!isLoading) return
        let i = 0
        const id = setInterval(() => {
            i = (i + 1) % LOADING_MESSAGES.length
            setLoadingMsg(LOADING_MESSAGES[i])
        }, 1800)
        return () => clearInterval(id)
    }, [isLoading])

    const fetchQuota = async () => {
        try {
            const data = await makeRequest("quota")
            setQuota(data)
        } catch (err) {
            console.log(err)
        }
    }

    const generateChallenge = async () => {
        setIsLoading(true)
        setError(null)
        setLoadingMsg(LOADING_MESSAGES[Math.floor(Math.random() * LOADING_MESSAGES.length)])

        try {
            const data = await makeRequest("generate-challenge", {
                method: "POST",
                body: JSON.stringify({difficulty})
            })
            setChallenge(data)
            fetchQuota()
        } catch (err) {
            setError(err.message || "No se pudo generar la pregunta.")
        } finally {
            setIsLoading(false)
        }
    }

    const getNextResetTime = () => {
        if (!quota?.last_reset_date) return null
        const resetDate = new Date(quota.last_reset_date)
        resetDate.setHours(resetDate.getHours() + 24)
        return resetDate
    }

    const remaining = quota?.quota_remaining ?? 0
    const noQuota = remaining === 0

    return <div className="challenge-container">
        <h2 className="section-title">Generador de preguntas</h2>
        <p className="section-subtitle">
            Preguntas tipo test al estilo del examen real de PER. Elige una dificultad y empieza a practicar.
        </p>

        <div className="quota-display">
            <div className="quota-icon" aria-hidden="true">⚡</div>
            <div className="quota-info">
                <div className="quota-label">Preguntas restantes hoy</div>
                <div className="quota-value">{remaining}</div>
            </div>
            {noQuota && getNextResetTime() && (
                <div className="quota-reset">
                    Próximo reset:<br/>
                    <strong>{getNextResetTime().toLocaleString("es-ES", {
                        hour: "2-digit", minute: "2-digit", day: "2-digit", month: "short"
                    })}</strong>
                </div>
            )}
        </div>

        <div className="difficulty-selector">
            <label className="difficulty-label">Dificultad</label>
            <div className="difficulty-pills" role="radiogroup" aria-label="Seleccionar dificultad">
                {DIFFICULTIES.map((d) => (
                    <button
                        key={d.id}
                        type="button"
                        role="radio"
                        aria-checked={difficulty === d.id}
                        className={`diff-pill ${d.className} ${difficulty === d.id ? "selected" : ""}`}
                        onClick={() => setDifficulty(d.id)}
                        disabled={isLoading}
                    >
                        <span className="diff-pill-name">
                            <span className="diff-pill-dot" aria-hidden="true"></span>
                            {d.name}
                        </span>
                        <span className="diff-pill-desc">{d.description}</span>
                    </button>
                ))}
            </div>
        </div>

        <button
            onClick={generateChallenge}
            disabled={isLoading || noQuota}
            className="generate-button"
        >
            {isLoading ? (
                <>
                    <span className="spinner" aria-hidden="true"></span>
                    <span>{loadingMsg}</span>
                </>
            ) : noQuota ? (
                <span>Has agotado tu cuota diaria</span>
            ) : (
                <>
                    <span>Generar pregunta</span>
                    <span aria-hidden="true">→</span>
                </>
            )}
        </button>

        {error && (
            <div className="error-message" role="alert">
                <span aria-hidden="true">⚠</span>
                <span>{error}</span>
            </div>
        )}

        {challenge && !isLoading && (
            <MCQChallenge key={challenge.id} challenge={challenge}/>
        )}
    </div>
}
