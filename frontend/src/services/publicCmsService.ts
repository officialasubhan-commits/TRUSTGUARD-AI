import axios from 'axios';
import { API_BASE_URL, API_TIMEOUT } from './apiConfig';
import {
  Contributor,
  ContributorsPageConfig,
  SystemSettingsConfig,
  WebsitePage,
} from '../types/admin';

export const publicApiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

export const publicCmsService = {
  async getContributors(): Promise<Contributor[]> {
    const res = await publicApiClient.get<Contributor[]>('/contributors');
    return res.data;
  },

  async getContributorsPageConfig(): Promise<ContributorsPageConfig> {
    const res = await publicApiClient.get<ContributorsPageConfig>('/contributors/page-config');
    return res.data;
  },

  async getPageBySlug(slug: string): Promise<WebsitePage> {
    const cleanSlug = slug.replace(/^\/|\/$/g, '');
    const res = await publicApiClient.get<WebsitePage>(`/pages/${cleanSlug}`);
    return res.data;
  },

  async getPublicSettings(): Promise<SystemSettingsConfig> {
    const res = await publicApiClient.get<SystemSettingsConfig>('/settings/public');
    return res.data;
  },
};
