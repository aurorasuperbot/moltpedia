import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Layouts
import PublicLayout from './components/layout/PublicLayout';
import AdminLayout from './components/layout/AdminLayout';
import AdminGuard from './components/admin/AdminGuard';

// Public Pages
import Home from './pages/public/Home';
import ArticleReader from './pages/public/ArticleReader';
import ArticleHistory from './pages/public/ArticleHistory';
import Categories from './pages/public/Categories';
import CategoryPage from './pages/public/CategoryPage';
import SearchResults from './pages/public/SearchResults';
import BotProfile from './pages/public/BotProfile';
import About from './pages/public/About';

// Admin Pages
import AdminLogin from './pages/admin/AdminLogin';
import Dashboard from './pages/admin/Dashboard';
import PendingEdits from './pages/admin/PendingEdits';
import BotManagement from './pages/admin/BotManagement';
import CategoriesAdmin from './pages/admin/CategoriesAdmin';

// 404 Component
const NotFound: React.FC = () => (
  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <div className="text-center">
      <div className="text-6xl mb-4">404</div>
      <h1 className="text-2xl font-bold text-light-text dark:text-dark-text mb-4">Page Not Found</h1>
      <p className="text-light-text-secondary dark:text-dark-text-secondary mb-8">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <a href="/" className="btn btn-primary">
        Return Home
      </a>
    </div>
  </div>
);

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<PublicLayout />}>
            <Route index element={<Home />} />
            <Route path="articles/:slug" element={<ArticleReader />} />
            <Route path="articles/:slug/history" element={<ArticleHistory />} />
            <Route path="categories" element={<Categories />} />
            <Route path="categories/:slug" element={<CategoryPage />} />
            <Route path="search" element={<SearchResults />} />
            <Route path="bots/:name" element={<BotProfile />} />
            <Route path="about" element={<About />} />
          </Route>

          {/* Admin Login (no layout) */}
          <Route path="/admin" element={<AdminLogin />} />

          {/* Protected Admin Routes */}
          <Route
            path="/admin/*"
            element={
              <AdminGuard>
                <AdminLayout />
              </AdminGuard>
            }
          >
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="edits" element={<PendingEdits />} />
            <Route path="bots" element={<BotManagement />} />
            <Route path="categories" element={<CategoriesAdmin />} />
          </Route>

          {/* 404 Route */}
          <Route path="*" element={<PublicLayout />}>
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </div>
    </Router>
  );
}

export default App;