import { Link, useLocation } from 'react-router-dom';
import { 
  Brain, 
  Home, 
  PlusCircle, 
  Layers, 
  Lightbulb, 
  BarChart3,
  RefreshCw,
  Sparkles,
  Map,
  GraduationCap,
  Network,
} from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

const navItems = [
  { path: '/', icon: Home, label: 'Dashboard' },
  { path: '/new', icon: PlusCircle, label: 'New Entry' },
  { path: '/review', icon: GraduationCap, label: 'Review (SRS)' },
  { path: '/graph', icon: Network, label: 'Knowledge Graph' },
  { path: '/recommendations', icon: Sparkles, label: 'Recommendations' },
  { path: '/plans', icon: Map, label: 'Learning Plans' },
  { path: '/patterns', icon: Layers, label: 'Patterns' },
  { path: '/recall', icon: Lightbulb, label: 'Recall' },
  { path: '/revision', icon: RefreshCw, label: 'Revision' },
  { path: '/analytics', icon: BarChart3, label: 'Analytics' },
];

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 text-white flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-gray-800">
          <Link to="/" className="flex items-center gap-3">
            <Brain className="w-8 h-8 text-indigo-400" />
            <div>
              <h1 className="text-xl font-bold">NeurOS</h1>
              <p className="text-xs text-gray-400">Metacognitive Retention System</p>
            </div>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            {navItems.map(({ path, icon: Icon, label }) => {
              const isActive = location.pathname === path;
              return (
                <li key={path}>
                  <Link
                    to={path}
                    className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-indigo-600 text-white'
                        : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-800">
          <p className="text-xs text-gray-500 text-center">
            Patterns over notes.
            <br />
            Retention over recall.
          </p>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-gray-950">
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
