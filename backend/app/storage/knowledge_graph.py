"""NetworkX-based knowledge graph for company relationships."""
import networkx as nx
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_company(self, ticker: str, name: str, sector: str, industry: str) -> None:
        self.graph.add_node(
            ticker,
            node_type="company",
            name=name,
            sector=sector,
            industry=industry,
        )

    def add_competitor_edge(self, from_ticker: str, to_ticker: str, source: str = "") -> None:
        self.graph.add_edge(
            from_ticker, to_ticker,
            edge_type="competitor",
            source=source,
        )

    def add_supplier_edge(self, supplier_ticker: str, customer_ticker: str) -> None:
        self.graph.add_edge(
            supplier_ticker, customer_ticker,
            edge_type="supplier_to",
        )

    def get_competitors(self, ticker: str) -> List[str]:
        """Return direct competitors."""
        competitors = []
        for _, neighbor, data in self.graph.edges(ticker, data=True):
            if data.get("edge_type") == "competitor":
                competitors.append(neighbor)
        # Also reverse edges
        for src, _, data in self.graph.in_edges(ticker, data=True):
            if data.get("edge_type") == "competitor" and src not in competitors:
                competitors.append(src)
        return competitors

    def get_industry_peers(self, ticker: str) -> List[str]:
        """Return nodes in the same industry."""
        if ticker not in self.graph.nodes:
            return []
        ticker_industry = self.graph.nodes[ticker].get("industry", "")
        peers = []
        for node, data in self.graph.nodes(data=True):
            if node != ticker and data.get("industry") == ticker_industry:
                peers.append(node)
        return peers

    def to_text_summary(self, ticker: str) -> str:
        """Format competitive landscape as text."""
        competitors = self.get_competitors(ticker)
        peers = self.get_industry_peers(ticker)
        lines = [f"# Competitive Landscape for {ticker}"]
        if competitors:
            lines.append(f"Direct competitors: {', '.join(competitors)}")
        if peers:
            lines.append(f"Industry peers: {', '.join(peers)}")
        if not competitors and not peers:
            lines.append("No competitor/peer data available in knowledge graph.")
        return "\n".join(lines)

    def clear(self) -> None:
        self.graph.clear()


# Global instance — populated during analysis
knowledge_graph = KnowledgeGraph()
