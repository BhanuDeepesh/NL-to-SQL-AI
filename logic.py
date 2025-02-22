import spacy
from typing import Dict, List, Set, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import yaml
import re
from collections import defaultdict
from spellchecker import SpellChecker
from difflib import get_close_matches

class SmartSchemaSystem:
    def __init__(self, nlp_model: str = "en_core_web_sm"):
        """Initialize the smart schema system with NLP components."""
        self.nlp = spacy.load(nlp_model)
        self.spell = SpellChecker()
        self.vectorizer = TfidfVectorizer(
            analyzer='word',
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )
        self.schema_vocabulary = set()
        self.context_words = set()
        
        # Semantic mappings
        self.semantic_mappings = {
            'purchase': ['order', 'transaction', 'buy'],
            'customer': ['user', 'client', 'buyer', 'account'],
            'product': ['item', 'goods', 'merchandise', 'inventory'],
            'payment': ['transaction', 'invoice', 'billing'],
            'shipping': ['delivery', 'shipment', 'transport'],
            'category': ['type', 'group', 'classification'],
            'price': ['cost', 'amount', 'value'],
            'date': ['time', 'when', 'timestamp'],
            'status': ['state', 'condition', 'phase'],
        }

    def _build_schema_vocabulary(self, schema: Dict) -> None:
        """Build vocabulary from schema structure."""
        vocabulary = set()
        context_words = set()
        
        for table_name, table_info in schema.items():
            table_parts = re.findall(r'[a-z]+', table_name.lower())
            vocabulary.update(table_parts)
            
            for column in table_info.get('columns', []):
                col_name = column.get('name', '').lower()
                vocabulary.update(re.findall(r'[a-z]+', col_name))
                
                if 'description' in column:
                    desc_words = re.findall(r'[a-z]+', column['description'].lower())
                    context_words.update(desc_words)
                    
                # Add context based on column type
                if 'id' in col_name:
                    context_words.update(['unique', 'identifier', 'reference'])
                elif 'date' in col_name:
                    context_words.update(['date', 'time', 'timestamp'])
                elif 'amount' in col_name:
                    context_words.update(['total', 'sum', 'price', 'cost'])
                    
        self.schema_vocabulary = vocabulary
        self.context_words = context_words
        self.spell.word_frequency.load_words(vocabulary)
        self.spell.word_frequency.load_words(context_words)

    def get_word_suggestions(self, word: str, schema: Dict) -> List[Tuple[str, float, str]]:
        """Get suggestions for potentially misspelled words."""
        if not self.schema_vocabulary:
            self._build_schema_vocabulary(schema)
            
        suggestions = []
        word_lower = word.lower()
        
        # Check exact matches
        if word_lower in self.schema_vocabulary:
            return [(word_lower, 1.0, 'exact')]
            
        # Get close matches
        schema_matches = get_close_matches(word_lower, self.schema_vocabulary, n=3, cutoff=0.6)
        context_matches = get_close_matches(word_lower, self.context_words, n=3, cutoff=0.6)
        
        for match in schema_matches:
            suggestions.append((match, 0.9, 'schema'))
        for match in context_matches:
            suggestions.append((match, 0.8, 'context'))
            
        # Add spelling suggestions
        spell_suggestions = self.spell.candidates(word_lower)
        for sugg in spell_suggestions:
            if sugg not in [s[0] for s in suggestions]:
                suggestions.append((sugg, 0.7, 'spelling'))
                
        return sorted(suggestions, key=lambda x: (-x[1], x[0]))[:3]

    def suggest_query_corrections(self, query: str, schema: Dict) -> List[Tuple[str, float, str]]:
        """Generate possible corrections for the query."""
        words = query.split()
        suggestions_per_word = {}
        
        for word in words:
            if not word.isalpha():
                continue
            
            suggestions = self.get_word_suggestions(word, schema)
            if suggestions:
                suggestions_per_word[word] = suggestions
                
        if not suggestions_per_word:
            return [(query, 1.0, 'original')]
            
        return self._generate_query_variations(words, suggestions_per_word)

    def _generate_query_variations(self, words: List[str], suggestions_per_word: Dict) -> List[Tuple[str, float, str]]:
        """Generate different versions of the corrected query."""
        variations = []
        
        # Best suggestions
        corrected = words.copy()
        confidence = 1.0
        for word, suggestions in suggestions_per_word.items():
            idx = words.index(word)
            corrected[idx] = suggestions[0][0]
            confidence *= suggestions[0][1]
        variations.append((' '.join(corrected), confidence, 'best_match'))
        
        # Alternative variations
        for i in range(1, 3):
            alt_words = words.copy()
            alt_confidence = 1.0
            for word, suggestions in suggestions_per_word.items():
                idx = words.index(word)
                if len(suggestions) > i:
                    alt_words[idx] = suggestions[i][0]
                    alt_confidence *= suggestions[i][1]
            variations.append((' '.join(alt_words), alt_confidence, f'alternative_{i}'))
            
        return sorted(variations, key=lambda x: x[1], reverse=True)

    def select_relevant_tables(self, query: str, schema: Dict, threshold: float = 0.1) -> Dict:
        """Select relevant tables based on the query."""
        # Build table contexts
        table_contexts = {}
        for table_name, table_info in schema.items():
            context = [table_name]
            
            # Add column names and descriptions
            for column in table_info.get('columns', []):
                context.append(column.get('name', ''))
                if 'description' in column:
                    context.append(column['description'])
                    
            table_contexts[table_name] = ' '.join(context).lower()
        
        # Vectorize and compare
        texts = [query.lower()] + list(table_contexts.values())
        tfidf_matrix = self.vectorizer.fit_transform(texts)
        
        # Calculate similarities
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]
        
        # Select relevant tables
        relevant_tables = {}
        for i, (table_name, _) in enumerate(table_contexts.items()):
            if similarities[i] >= threshold:
                relevant_tables[table_name] = {
                    **schema[table_name],
                    'relevance_score': float(similarities[i])
                }
                
        return relevant_tables

    def process_query(self, query: str, schema: Dict) -> Tuple[str, Dict]:
        """Process query with corrections and table selection."""
        # Get query corrections
        corrections = self.suggest_query_corrections(query, schema)
        best_correction = corrections[0][0]
        
        # Select relevant tables
        relevant_tables = self.select_relevant_tables(best_correction, schema)
        
        return best_correction, relevant_tables

def main():
    """Example usage"""
    # Sample schema
    sample_schema = {
        "orders": {
            "columns": [
                {"name": "order_id", "type": "integer", "description": "Unique order identifier"},
                {"name": "user_id", "type": "integer", "description": "Reference to users table"},
                {"name": "order_date", "type": "date", "description": "Date when order was placed"},
                {"name": "total_amount", "type": "decimal", "description": "Total order amount"}
            ]
        },
        "users": {
            "columns": [
                {"name": "user_id", "type": "integer", "description": "Unique user identifier"},
                {"name": "username", "type": "string", "description": "User's display name"},
                {"name": "email", "type": "string", "description": "User's email address"}
            ]
        },
        "products": {
            "columns": [
                {"name": "product_id", "type": "integer", "description": "Unique product identifier"},
                {"name": "name", "type": "string", "description": "Product name"},
                {"name": "price", "type": "decimal", "description": "Product price"},
                {"name": "category", "type": "string", "description": "Product category"}
            ]
        }
    }
    
    # Initialize system
    system = SmartSchemaSystem()
    
    print("Smart Schema Analysis System")
    print("Enter queries to get corrections and relevant tables")
    print("Type 'quit' to exit\n")
    
    while True:
        try:
            query = input("Query: ").strip()
            
            if not query:
                print("Please enter a query")
                continue
                
            if query.lower() == 'quit':
                break
                
            # Process query
            corrections = system.suggest_query_corrections(query, sample_schema)
            
            # Show corrections
            print("\nPossible corrections:")
            for i, (correction, score, source) in enumerate(corrections, 1):
                if correction != query:
                    print(f"{i}. {correction}")
                    print(f"   Confidence: {score:.2f}")
                    print(f"   Source: {source}")
            
            # Get user choice
            if len(corrections) > 1:
                while True:
                    choice = input("\nSelect correction (1-3) or press Enter to keep original: ").strip()
                    if not choice:
                        selected_query = query
                        break
                    try:
                        idx = int(choice) - 1
                        if 0 <= idx < len(corrections):
                            selected_query = corrections[idx][0]
                            break
                    except ValueError:
                        pass
                    print("Invalid choice. Please try again.")
            else:
                selected_query = query
            
             #Get relevant tables
            relevant_tables = system.select_relevant_tables(selected_query, sample_schema)
            
            print(f"\nUsing query: {selected_query}")
            print("\nRelevant tables:")
            for table_name, table_info in relevant_tables.items():
                score = table_info.get('relevance_score', 0.0)
                print(f"\n- {table_name} (relevance: {score:.2f})")
                print("  Columns:")
                for column in table_info['columns']:
                    print(f"    - {column['name']}: {column['type']}")
                    if 'description' in column:
                        print(f"      {column['description']}")
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue

if __name__ == "__main__":
    main()