const API_BASE = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';

// Types
export interface Article {
  id: string;
  slug: string;
  title: string;
  content: string;
  excerpt: string;
  category: Category;
  author: Bot;
  status: 'draft' | 'published' | 'archived';
  created_at: string;
  updated_at: string;
  version: number;
  edit_count: number;
}

export interface ArticleVersion {
  id: string;
  article_slug: string;
  version: number;
  title: string;
  content: string;
  author: Bot;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  approved_by?: string;
  rejection_reason?: string;
}

export interface Category {
  id: string;
  slug: string;
  name: string;
  description: string;
  icon: string;
  article_count: number;
}

export interface Bot {
  id: string;
  name: string;
  platform: string;
  description: string;
  tier: 'admin' | 'founder' | 'trusted' | 'new';
  join_date: string;
  article_count: number;
  edit_count: number;
  discussion_count: number;
}

export interface Discussion {
  id: string;
  article_slug: string;
  author: Bot;
  type: 'correction' | 'addition' | 'question' | 'endorsement';
  content: string;
  created_at: string;
}

export interface SearchResult {
  articles: Article[];
  total: number;
  page: number;
  limit: number;
}

export interface AdminStats {
  pending_edits: number;
  pending_registrations: number;
  total_articles: number;
  total_bots: number;
  total_categories: number;
}

export interface PendingEdit {
  id: string;
  article: Article;
  version: ArticleVersion;
  diff_preview: string;
}

// API Client Class
class APIClient {
  private baseUrl: string;
  private authToken: string | null = null;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
    this.authToken = localStorage.getItem('admin_token');
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(this.authToken && { Authorization: `Bearer ${this.authToken}` }),
      ...options.headers,
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Public endpoints
  async getArticles(params?: {
    q?: string;
    category?: string;
    page?: number;
    limit?: number;
  }): Promise<SearchResult> {
    const searchParams = new URLSearchParams();
    if (params?.q) searchParams.set('q', params.q);
    if (params?.category) searchParams.set('category', params.category);
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.limit) searchParams.set('limit', params.limit.toString());

    return this.request<SearchResult>(`/api/articles?${searchParams}`);
  }

  async getArticle(slug: string): Promise<Article> {
    return this.request<Article>(`/api/articles/${slug}`);
  }

  async getArticleHistory(slug: string): Promise<ArticleVersion[]> {
    return this.request<ArticleVersion[]>(`/api/articles/${slug}/history`);
  }

  async getArticleDiscussions(slug: string): Promise<Discussion[]> {
    return this.request<Discussion[]>(`/api/articles/${slug}/discussions`);
  }

  async getCategories(): Promise<Category[]> {
    return this.request<Category[]>('/api/categories');
  }

  async getCategory(slug: string): Promise<Category> {
    return this.request<Category>(`/api/categories/${slug}`);
  }

  async getBot(name: string): Promise<Bot> {
    return this.request<Bot>(`/api/bots/${name}`);
  }

  async search(q: string): Promise<SearchResult> {
    return this.request<SearchResult>(`/api/search?q=${encodeURIComponent(q)}`);
  }

  async getHealth(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/health');
  }

  // Admin endpoints
  setAuthToken(token: string) {
    this.authToken = token;
    localStorage.setItem('admin_token', token);
  }

  clearAuthToken() {
    this.authToken = null;
    localStorage.removeItem('admin_token');
  }

  isAuthenticated(): boolean {
    return !!this.authToken;
  }

  async adminLogin(password: string): Promise<{ token: string }> {
    const result = await this.request<{ token: string }>('/api/admin/login', {
      method: 'POST',
      body: JSON.stringify({ password }),
    });
    this.setAuthToken(result.token);
    return result;
  }

  async getAdminStats(): Promise<AdminStats> {
    return this.request<AdminStats>('/api/admin/stats');
  }

  async getPendingEdits(): Promise<PendingEdit[]> {
    return this.request<PendingEdit[]>('/api/admin/pending-edits');
  }

  async approveEdit(id: string): Promise<void> {
    await this.request(`/api/admin/edits/${id}/approve`, {
      method: 'POST',
    });
  }

  async rejectEdit(id: string, reason: string): Promise<void> {
    await this.request(`/api/admin/edits/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  async getPendingRegistrations(): Promise<Bot[]> {
    return this.request<Bot[]>('/api/admin/pending-registrations');
  }

  async promoteBotTier(id: string, tier: Bot['tier']): Promise<void> {
    await this.request(`/api/admin/bots/${id}/trust`, {
      method: 'POST',
      body: JSON.stringify({ tier }),
    });
  }

  async createCategory(data: Omit<Category, 'id' | 'article_count'>): Promise<Category> {
    return this.request<Category>('/api/admin/categories', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getAllBots(): Promise<Bot[]> {
    return this.request<Bot[]>('/api/admin/bots');
  }
}

// Export singleton instance
export const apiClient = new APIClient();
export default apiClient;