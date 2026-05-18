import "react"
import {SignedIn, SignedOut, UserButton} from "@clerk/clerk-react"
import {Outlet, Link, Navigate, useLocation} from "react-router-dom"

export function Layout() {
    const location = useLocation()
    const isActive = (path) => location.pathname === path

    return <div className="app-layout">
        <header className="app-header">
            <div className="header-content">
                <Link to="/" className="brand">
                    <div className="brand-logo">P</div>
                    <div>
                        <h1>PER Quiz</h1>
                        <div className="brand-subtitle">Prepara tu examen</div>
                    </div>
                </Link>
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
                                    avatarBox: { width: "32px", height: "32px" }
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
}
