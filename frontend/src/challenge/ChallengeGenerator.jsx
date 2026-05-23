import "react"
import {useState, useEffect} from "react"
import {MCQChallenge} from "./MCQChallenge.jsx"
import {useApi} from "../utils/api.js"
import {useSubject} from "../utils/SubjectContext.jsx"

const DIFFICULTIES = [
    {id: "easy",   name: "Fácil",   className: "easy"},
    {id: "medium", name: "Medio",   className: "medium"},
    {id: "hard",   name: "Difícil", className: "hard"},
]

// Descripciones contextualizadas por asignatura para que se note que la
// app sabe en qué estás.
const DIFFICULTY_DESCRIPTIONS = {
    per: {
        easy:   "Conceptos básicos: clases, verbos HTTP, JSON",
        medium: "Herencia, REST, sockets, loads vs load",
        hard:   "Análisis de código, traza HTTP, override avanzado",
    },
    biochem: {
        easy:   "Conceptos clave: enzimas, código genético, replicación",
        medium: "Mecanismos: transcripción, traducción, operones",
        hard:   "Regulación eucariota, ingeniería genética, CRISPR",
    },
}

// Mensajes de carga rotativos, también contextualizados.
const LOADING_MESSAGES = {
    per: [
        "Consultando el temario de PER...",
        "Diseñando distractores plausibles...",
        "Buscando ese bug sutil en el código...",
        "Revisando los apuntes de la URJC...",
        "Eligiendo el nivel adecuado de trampa...",
    ],
    biochem: [
        "Consultando el temario de bioquímica...",
        "Repasando los temas 14 a 18...",
        "Diseñando distractores plausibles...",
        "Revisando los apuntes de la profesora...",
        "Buscando ese matiz que separa los conceptos...",
    ],
}

const FALLBACK_LOADING = ["Generando pregunta..."]

export function ChallengeGenerator() {
    const [challenge, setChallenge] = useState(null)
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState(null)
    const [difficulty, setDifficulty] = useState("easy")
    const [quota, setQuota] = useState(null)
    const [loadingMsg, setLoadingMsg] = useState("")
    const {makeRequest} = useApi()
    const {activeSubject, activeMeta} = useSubject()

    // Cada vez que cambia la asignatura, limpiamos la pregunta visible
    // (no tiene sentido seguir viendo una de bioquímica al pasar a PER).
    useEffect(() => {
        setChallenge(null)
        setError(null)
    }, [activeSubject])

    useEffect(() => {
        fetchQuota()
    }, [])

    // Rotación de mensajes de carga mientras se genera
    useEffect(() => {
        if (!isLoading) return
        const pool = LOADING_MESSAGES[activeSubject] || FALLBACK_LOADING
        let i = Math.floor(Math.random() * pool.length)
        setLoadingMsg(pool[i])
        const id = setInterval(() => {
            i = (i + 1) % pool.length
            setLoadingMsg(pool[i])
        }, 1800)
        return () => clearInterval(id)
    }, [isLoading, activeSubject])

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
        try {
            const data = await makeRequest("generate-challenge", {
                method: "POST",
                body: JSON.stringify({difficulty, subject: activeSubject}),
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
    const descriptions = DIFFICULTY_DESCRIPTIONS[activeSubject] || DIFFICULTY_DESCRIPTIONS.per

    return (
        <div className="challenge-container">
            <h2 className="section-title">Generador de preguntas</h2>
            <p className="section-subtitle">
                Preguntas tipo test al estilo del examen real de{" "}
                <strong>{activeMeta?.full_name || activeMeta?.name || activeSubject}</strong>.
                Elige una dificultad y empieza a practicar.
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
                            <span className="diff-pill-desc">{descriptions[d.id]}</span>
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
    )
}