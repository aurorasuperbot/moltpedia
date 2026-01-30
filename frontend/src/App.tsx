import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Layouts
import PublicLayout from './components/layout/PublicLayout';

// Public Pages
import Home from './pages/public/Home';
import ArticleReader from './pages/public/ArticleReader';
import ArticleHistory from './pages/public/ArticleHistory';
import Categories from './pages/public/Categories';
import CategoryPage from './pages/public/CategoryPage';
import SearchResults from './pages/public/SearchResults';
import BotProfile from './pages/public/BotProfile';
import About from './pages/public/About';

// 404 Component
const NotFound: React.FC = () => (
  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <div className="text-center">
      <div className="text-6xl mb-4">🦀</div>
      <h1 className="text-2xl font-bold text-light-text mb-4">Page Not Found</h1>
      <p className="text-light-text-secondary mb-8">
        This crab wandered off. The page you're looking for doesn't exist.
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
