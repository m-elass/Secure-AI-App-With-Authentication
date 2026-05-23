import "react"
import {SignedIn, SignedOut, UserButton} from "@clerk/clerk-react"
import {Outlet, Link, Navigate, useLocation} from "react-router-dom"
import {useSubject} from "../utils/SubjectContext.jsx"

export function Layout() {
    const location = useLocation()
    const {subjects, activeSubject, activeMeta, setActiveSubject} = useSubject()
    const isActive = (path) => location.pathname === path

    return (
        <div className="app-layout">
            <header className="app-header">
                <div className="header-content">
                    <Link to="/" className="brand">
                        <div className="brand-logo">P</div>
                        <div>
                            <h1>PER Quiz</h1>
                            <div className="brand-subtitle">
                                {activeMeta?.full_name || "Prepara tu examen"}
                            </div>
                        </div>
                    </Link>

                    <SignedIn>
                        <div className="subject-switch" role="tablist" aria-label="Asignatura">
                            {subjects.map((s) => (
                                <button
                                    key={s.id}
                                    type="button"
                                    role="tab"
                                    aria-selected={activeSubject === s.id}
                                    className={`subject-tab ${activeSubject === s.id ? "active" : ""}`}
                                    data-accent={s.accent}
                                    onClick={() => setActiveSubject(s.id)}
                                    title={s.full_name}
                                >
                                    {s.name}
                                </button>
                            ))}
                        </div>
                    </SignedIn>

                    <nav>
                        <SignedIn>
                            <Link to="/" className={isActive("/") ? "active" : ""}>
                                Generar
                            </Link>
                            <Link to="/history" className={isActive("/history") ? "active" : ""}>
                                Historial
                            </Link>
                            <UserButton
                                appearance={{
                                    elements: {
                                        avatarBox: {width: "32px", height: "32px"}
                                    }
                                }}
                            />
                        </SignedIn>
                    </nav>
                </div>
            </header>

            <main className="app-main">
                <SignedOut>
                    <Navigate to="/sign-in" replace/>
                </SignedOut>
                <SignedIn>
                    <Outlet />
                </SignedIn>
            </main>
        </div>
    )
}