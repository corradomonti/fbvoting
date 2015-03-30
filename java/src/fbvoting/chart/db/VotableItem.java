package fbvoting.chart.db;

import it.unimi.dsi.fastutil.objects.Object2IntMap;
import it.unimi.dsi.fastutil.objects.Object2IntOpenHashMap;
import it.unimi.dsi.fastutil.objects.Object2ObjectMap;
import it.unimi.dsi.fastutil.objects.Object2ObjectOpenHashMap;

import com.mongodb.BasicDBObject;
import com.mongodb.DBObject;

public class VotableItem {
	
	private static final Object2ObjectMap<String, VotableItem> pool
		= new Object2ObjectOpenHashMap<String, VotableItem>();
	
	public static VotableItem from(DBObject itemInDb) {
		String author = (String) itemInDb.get("author");
		String song = (String) itemInDb.get("song");
		
		String poolKey = author + '%' + song;
		VotableItem item = pool.get(poolKey);
		if (item == null) {
			item = new VotableItem(author, song);
			pool.put(poolKey, item);
		}
		
		if (itemInDb.containsField("video"))
			item.addVideo((String) itemInDb.get("video"));
		
		return item;
	}
	
	private final String author, song;
	private final Object2IntOpenHashMap<String> videos = new Object2IntOpenHashMap<String>();
	
	private VotableItem (String author, String song) {
		this.author = author;
		this.song = song;
		videos.defaultReturnValue(0);
	}
	
	public String toString() {
		return author + " - " + song;
	}
	
	private void addVideo(String videoId) {
		videos.addTo(videoId, 1);
	}
	
	private String getMostAssociatedVideo() throws NoVideoAssociatedException {
		int maxNumberOfAssociation = 0;
		String result = null;
		
		for (Object2IntMap.Entry<String> video : videos.object2IntEntrySet()) {
			if (video.getIntValue() > maxNumberOfAssociation) {
				maxNumberOfAssociation = video.getIntValue();
				result = video.getKey();
			}
		}
		
		if (result == null)
			throw new NoVideoAssociatedException();
		
		return result;
	}
	
	public DBObject toDBObject() throws NoVideoAssociatedException {
		return new BasicDBObject
				   ("author", author)
			.append("song", song)
			.append("video", getMostAssociatedVideo());
	}

	@Override
	public int hashCode() {
		final int prime = 31;
		int result = 1;
		result = prime * result + ((author == null) ? 0 : author.hashCode());
		result = prime * result + ((song == null) ? 0 : song.hashCode());
		return result;
	}

	@Override
	public boolean equals(Object obj) {
		if (this == obj)
			return true;
		if (obj == null)
			return false;
		if (getClass() != obj.getClass())
			return false;
		VotableItem other = (VotableItem) obj;
		if (author == null) {
			if (other.author != null)
				return false;
		} else if (!author.equals(other.author))
			return false;
		if (song == null) {
			if (other.song != null)
				return false;
		} else if (!song.equals(other.song))
			return false;
		return true;
	}
	
	@SuppressWarnings("serial")
	protected static class NoVideoAssociatedException extends Exception {
	}
}
