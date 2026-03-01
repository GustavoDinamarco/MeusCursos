import { Link, useLocation } from "react-router-dom";
import { BookOpen, Home, Settings } from "lucide-react";

interface HeaderProps {
  variant?: "full" | "minimal";
}

const Header = ({ variant = "full" }: HeaderProps) => {
  const location = useLocation();

  return (
    <header className="fixed top-0 z-50 w-full glass-header border-b border-white/10">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
            <BookOpen className="h-5 w-5 text-primary-foreground" />
          </div>
          <span className="text-lg font-bold text-gradient">MeusCursos</span>
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          {variant === "full" ? (
            <>
              <Link
                to="/"
                className={`flex items-center gap-2 text-sm font-medium transition-colors ${
                  location.pathname === "/"
                    ? "text-primary"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Home className="h-4 w-4" />
                Home
              </Link>
              <Link
                to="/admin"
                className={`flex items-center gap-2 text-sm font-medium transition-colors ${
                  location.pathname === "/admin"
                    ? "text-primary"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Settings className="h-4 w-4" />
                Gerenciar
              </Link>
            </>
          ) : (
            <Link
              to="/"
              className="flex items-center gap-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              <Home className="h-4 w-4" />
              Meus Cursos
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
};

export default Header;
