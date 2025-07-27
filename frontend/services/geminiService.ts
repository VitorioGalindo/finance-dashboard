import { GoogleGenAI } from "@google/genai";
import { CompanyNewsItem } from '../types';

const API_KEY = process.env.API_KEY;

if (!API_KEY) {
    throw new Error("API_KEY environment variable not set.");
}

const ai = new GoogleGenAI({ apiKey: API_KEY });
const model = 'gemini-2.5-flash';

const streamFinancialAnalysis = async function* (prompt: string, systemInstruction: string) {
    try {
        const result = await ai.models.generateContentStream({
            model: model,
            contents: prompt,
            config: {
                systemInstruction: systemInstruction,
            },
        });

        for await (const chunk of result) {
            if(chunk.text) {
               yield chunk.text;
            }
        }
    } catch (error) {
        console.error("Error in Gemini stream:", error);
        yield "Ocorreu um erro ao comunicar com a IA. Por favor, tente novamente.";
    }
};

const summarizeNewsFromUrl = async (url: string): Promise<Omit<CompanyNewsItem, 'id' | 'url'>> => {
    console.log(`Simulating Gemini analysis for URL: ${url}`);
    
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1500));

    // In a real application, you would make a call to your backend,
    // which then calls the Gemini API with the content of the URL.
    // Here, we return mock data based on a fictional URL.
    
    const mockData = {
        title: "Microsoft Earnings: Good Quarter From Any Angle",
        summary: "A Microsoft divulgou um trimestre sólido, superando as expectativas em todas as frentes. O crescimento da receita de nuvem (Azure) continua a ser o principal impulsionador, com um aumento de 29% em relação ao ano anterior. A empresa também viu força em seus segmentos de produtividade e computação pessoal.",
        source: "Morningstar",
        publishedDate: new Date().toISOString(),
    };
    
    return mockData;
};


export const geminiService = {
    streamFinancialAnalysis,
    summarizeNewsFromUrl,
};