import "react"
import {createContext, useContext, useEffect, useState, useCallback} from "react"

/**
 * SubjectContext — guarda la asignatura activa del usuario, persistente
 * entre sesiones gracias a localStorage.
 *
 * La asignatura activa controla:
 *   - El branding (acentos de color en CSS, vía atributo data-subject)
 *   - El subject enviado en las peticiones de generación
 *   - El filtro del historial
 *
 * Las asignaturas disponibles las descubrimos llamando al endpoint
 * /subjects al arrancar; así si añades una nueva asignatura en el backend
 * basta con desplegar — el frontend la pilla sola.
 */

const SUBJECT_STORAGE_KEY = "perquiz.activeSubject"
const DEFAULT_SUBJECT = "per"

// Lista de "seed" — se usa hasta que /subjects responda. Permite que la
// UI funcione aunque el backend no responda inmediatamente.
const SEED_SUBJECTS = [
    {
        id: "per",
        name: "PER",
        full_name: "Programación en Entornos de Red",
        description: "Python OOP, HTTP, sockets, JSON",
        accent: "violet",
    },
    {
        id: "biochem",
        name: "Bioquímica",
        full_name: "Bioquímica y Biología Molecular",
        description: "Replicación, transcripción, traducción, regulación, ingeniería genética",
        accent: "emerald",
    },
]

const SubjectContext = createContext(null)

export function SubjectProvider({children, apiClient}) {
    const [subjects, setSubjects] = useState(SEED_SUBJECTS)
    const [activeSubject, setActiveSubjectState] = useState(() => {
        try {
            const stored = localStorage.getItem(SUBJECT_STORAGE_KEY)
            return stored || DEFAULT_SUBJECT
        } catch {
            return DEFAULT_SUBJECT
        }
    })

    // Carga inicial del catálogo de asignaturas desde el backend
    useEffect(() => {
        if (!apiClient) return
        apiClient("subjects")
            .then((data) => {
                if (data?.subjects?.length) {
                    setSubjects(data.subjects)
                    // Si la asignatura guardada en localStorage ya no existe,
                    // caemos a la primera disponible.
                    if (!data.subjects.find(s => s.id === activeSubject)) {
                        setActiveSubjectState(data.subjects[0].id)
                    }
                }
            })
            .catch((err) => {
                console.warn("No se pudieron cargar las asignaturas:", err)
                // Mantenemos las seed.
            })
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [apiClient])

    // Sincroniza atributo data-subject en <body> y localStorage
    useEffect(() => {
        try {
            localStorage.setItem(SUBJECT_STORAGE_KEY, activeSubject)
        } catch {
            // localStorage puede no estar disponible (modo privado); seguimos.
        }
        const meta = subjects.find(s => s.id === activeSubject)
        if (meta) {
            document.body.dataset.subject = activeSubject
            document.body.dataset.accent = meta.accent
        }
    }, [activeSubject, subjects])

    const setActiveSubject = useCallback((id) => {
        if (subjects.find(s => s.id === id)) {
            setActiveSubjectState(id)
        }
    }, [subjects])

    const activeMeta = subjects.find(s => s.id === activeSubject) || subjects[0]

    const value = {
        subjects,
        activeSubject,
        activeMeta,
        setActiveSubject,
    }

    return (
        <SubjectContext.Provider value={value}>
            {children}
        </SubjectContext.Provider>
    )
}

export function useSubject() {
    const ctx = useContext(SubjectContext)
    if (!ctx) {
        throw new Error("useSubject debe usarse dentro de un SubjectProvider")
    }
    return ctx
}