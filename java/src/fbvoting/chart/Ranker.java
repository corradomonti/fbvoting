package fbvoting.chart;

import it.unimi.dsi.fastutil.longs.Long2DoubleMap;
import it.unimi.dsi.fastutil.longs.Long2DoubleOpenHashMap;
import it.unimi.dsi.law.rank.KatzParallelGaussSeidel;
import it.unimi.dsi.law.rank.SpectralRanking;
import it.unimi.dsi.webgraph.Transform;

import java.io.IOException;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Ranker {
	
	private final static Logger LOGGER = LoggerFactory.getLogger(Ranker.class);
	
	private final Voting votes;
	private final KatzParallelGaussSeidel rankingStrategy;
	
	public Ranker(Voting votes, double alpha) {
		LOGGER.info("Preparing ranking process...");
		this.votes = votes;
		rankingStrategy = new KatzParallelGaussSeidel(
				Transform.transpose(votes.graph())
			);
		rankingStrategy.alpha = alpha;
	}
	
	public Long2DoubleMap computeRank() throws IOException {
		LOGGER.info("Starting to rank...");
		rankingStrategy.stepUntil(new SpectralRanking.NormStoppingCriterion((1E-10)));
		return convert(rankingStrategy.rank, votes.ids());
	}
	
	private static Long2DoubleMap convert(double[] rank, long[] ids) {
		LOGGER.info("Converting graph ranks to id -> rank map...");
		
		Long2DoubleMap map = new Long2DoubleOpenHashMap(ids, rank);
		map.defaultReturnValue( 1.0 );
		
		LOGGER.info("id -> rank map completed.");
		
		return map;
	}

}
